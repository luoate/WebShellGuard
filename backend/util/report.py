import re
import os
import base64
import zlib

class WebShellAnalyzer:
    """PHP WebShell 分析器类，用于检测和分析潜在的 PHP WebShell 威胁"""
    
    # 定义危险函数和相关类别
    DANGEROUS_FUNCTIONS = [
        "eval", "exec", "system", "passthru", "shell_exec", "popen",
        "proc_open", "assert", "base64_decode", "gzinflate", "gzuncompress", 
        "str_rot13", "create_function"
    ]
    FILE_OP_FUNCS = ["file_put_contents", "fwrite", "fopen", "unlink", "chmod", "copy"]
    NETWORK_FUNCS = ["curl_exec", "fsockopen", "file_get_contents", "curl_multi_exec"]
    OBFUSCATION_PATTERNS = ['str_rot13', 'gzuncompress', 'gzinflate']

    def __init__(self, file_path, file_info = None):
        """初始化分析器，加载文件内容"""
        self.file_path = file_path
        self.file_info = file_info
        self.content = self._load_file()
        self.dynamic_funcs = {}
        self.executed_code = None
        self.decoded_payload = None

    def _load_file(self):
        """加载并读取 PHP 文件内容"""
        with open(self.file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()

    def detect_base64_strings(self):
        """检测潜在的 base64 编码字符串"""
        base64_pattern = re.compile(r'["\']?([A-Za-z0-9+/]{50,}={0,2})["\']?')
        return base64_pattern.findall(self.content)

    def extract_eval_base64_blocks(self):
        """提取并解码 eval(base64_decode(...)) 块"""
        pattern = re.compile(r"eval\s*\(\s*base64_decode\s*\(\s*[\"']([^\"']{20,})[\"']\s*\)\s*\)")
        matches = pattern.findall(self.content)
        decoded_blocks = []
        for b64_str in matches:
            try:
                decoded = base64.b64decode(b64_str).decode('utf-8', errors='ignore')
                decoded_blocks.append(decoded.strip())
            except Exception as e:
                decoded_blocks.append(f"(解码失败: {str(e)})")
        return decoded_blocks

    def detect_dynamic_function_names(self):
        """检测通过 str_replace 动态生成的函数名"""
        pattern = re.compile(r"\$(\w+)\s*=\s*str_replace\(['\"](.)['\"],\s*['\"]['\"],['\"]([^'\"]+)['\"]\);")
        matches = pattern.findall(self.content)
        dynamic_funcs = {}
        for match in matches:
            var_name = match[0]
            replace_char = match[1]
            original_str = match[2]
            func_name = original_str.replace(replace_char, '')
            dynamic_funcs[var_name] = func_name
        self.dynamic_funcs = dynamic_funcs
        return dynamic_funcs

    def detect_preg_replace_eval(self):
        """检测 preg_replace 中是否使用了动态函数执行 eval"""
        pattern = re.compile(r"preg_replace\(['\"]([^'\"]+)['\"],['\"]([^'\"]+)['\"],['\"]([^'\"]+)['\"]\);")
        matches = pattern.findall(self.content)
        for match in matches:
            pattern_str = match[0]
            replacement_str = match[1]
            subject_str = match[2]
            if 'eval' in replacement_str.lower():
                for var, func in self.dynamic_funcs.items():
                    if var in replacement_str:
                        self.executed_code = replacement_str.replace(var, func)
                        return self.executed_code
        return None

    def decode_and_decompress(self, enfile):
        """尝试解码和解压 base64 编码的压缩 payload"""
        try:
            decoded = base64.b64decode(enfile)
            decompressed = zlib.decompress(decoded, -15).decode('utf-8', errors='ignore')
            return decompressed
        except Exception:
            return None

    def decode_payload_chain(self):
        """尝试递归解码完整 payload 链"""
        if not self.executed_code:
            return None
        var_match = re.search(r"\$(\w+)\s*=\s*['\"](.+?)['\"]\s*;", self.content)
        if not var_match:
            return None
        enfile_var = var_match.group(1)
        enfile_value = var_match.group(2)
        if enfile_var in self.executed_code:
            self.decoded_payload = self.recursive_decode_chain(enfile_value)
            return self.decoded_payload
        return None
    
    def classify(self):
        """根据检测到的特征对 WebShell 进行分类"""
        categories = []

        # 检测命令执行型
        cmd_exec_funcs = ["exec", "system", "passthru", "shell_exec", "popen", "proc_open"]
        if any(re.search(rf"\b{func}\b", self.content) for func in cmd_exec_funcs):
            categories.append("命令执行型")

        # 检测文件操作型
        if any(re.search(rf"\b{func}\b", self.content) for func in self.FILE_OP_FUNCS):
            categories.append("文件操作型")

        # 检测网络通信型
        if any(re.search(rf"\b{func}\b", self.content) for func in self.NETWORK_FUNCS):
            categories.append("网络通信型")

        # 检测混淆型
        if any(re.search(rf"\b{func}\b", self.content) for func in self.OBFUSCATION_PATTERNS):
            categories.append("混淆型")

        # 如果同时属于 3 个或更多类别，则归类为多功能型
        if len(categories) >= 3:
            return "多功能型"
        elif categories:
            return "、".join(categories)
        else:
            return "未知类型"


    def calculate_threat_level(self):
        """计算威胁等级"""
        dangerous_funcs = [func for func in self.DANGEROUS_FUNCTIONS if re.search(rf"\b{func}\b", self.content)]
        file_funcs = [func for func in self.FILE_OP_FUNCS if re.search(rf"\b{func}\b", self.content)]
        net_funcs = [func for func in self.NETWORK_FUNCS if re.search(rf"\b{func}\b", self.content)]
        has_b64 = len(self.detect_base64_strings()) > 0
        eval_b64 = bool(re.search(r"eval\s*\(\s*base64_decode", self.content))
        create_func = bool(re.search(r"create_function\s*\(", self.content))
        obfuscation_found = any(re.search(rf"\b{func}\b", self.content) for func in self.OBFUSCATION_PATTERNS)

        score = min(len(dangerous_funcs), 5)
        if has_b64:
            score += 1
        if eval_b64:
            score += 2
        if create_func:
            score += 1
        if file_funcs:
            score += 1
        if net_funcs:
            score += 1
        if obfuscation_found:
            score += 1
        if self.dynamic_funcs and self.executed_code:
            score += 2  # 动态生成函数并执行 eval 的高危模式
        if len(self.content) < 200 and any(func in self.content for func in ['eval', 'assert', 'create_function']):
            score = max(score, 7)
        return min(score, 10)
    
    def recursive_decode_chain(self, payload):
        """递归尝试多种编码链解码"""
        current = payload
        try:
            while True:
                if isinstance(current, str):
                    current = current.encode()
                # base64
                if re.fullmatch(b'[A-Za-z0-9+/=]{20,}', current.strip()):
                    current = base64.b64decode(current)
                    continue
                # gzinflate
                try:
                    decompressed = zlib.decompress(current, -15)
                    current = decompressed
                    continue
                except zlib.error:
                    pass
                # gzuncompress
                try:
                    decompressed = zlib.decompress(current)
                    current = decompressed
                    continue
                except zlib.error:
                    pass
                break
        except Exception as e:
            return f"(递归解码失败: {e})"
        return current.decode('utf-8', errors='ignore')


    def threat_description(self, score):
        """根据威胁等级返回描述"""
        if score >= 8:
            return "⚠️ 高风险：该 WebShell 具备强大的命令执行与隐藏能力，可能用于持续控制服务器。建议立即隔离主机，并进行全面排查。"
        elif score >= 5:
            return "⚠️ 中风险：WebShell 包含多个危险调用，具备一定危害性，需详细审计行为并清除残留。"
        else:
            return "🟡 低风险：虽然为 WebShell，但功能较简单，仍建议谨慎处理。"
        # else:
        #     return "✅ 安全：虽然指定为 WebShell，但没有明显恶意特征，可能为误判或被混淆绕过。"

    def analyze(self):
        """执行完整分析并生成报告"""
        report = []
        filename = os.path.basename(self.file_path)
        report.append(f"# WebShell 分析报告：{filename}\n")

        # 加入文件基本信息
        report.append("## 文件基本信息")
        if self.file_info:
            for info in self.file_info:
                report.append(f"- **{info}：**`{self.file_info[info]}`")
        else:
            report.append("- 无")

        # 检测危险函数
        found_funcs = [func for func in self.DANGEROUS_FUNCTIONS if re.search(rf"\b{func}\b", self.content)]
        report.append("## 危险函数使用")
        if found_funcs:
            for func in found_funcs:
                report.append(f"- `{func}`")
        else:
            report.append("- 无")

        # 文件和网络函数
        file_funcs = [func for func in self.FILE_OP_FUNCS if re.search(rf"\b{func}\b", self.content)]
        net_funcs = [func for func in self.NETWORK_FUNCS if re.search(rf"\b{func}\b", self.content)]
        report.append("\n## 文件操作函数")
        report.append(", ".join(file_funcs) if file_funcs else "无")
        report.append("\n## 网络函数")
        report.append(", ".join(net_funcs) if net_funcs else "无")

        # Base64 检测
        b64s = self.detect_base64_strings()
        report.append("\n## Base64 编码片段")
        if b64s:
            for i, b64 in enumerate(b64s[:3]):
                report.append(f"- `{b64[:60]}...`")
        else:
            report.append("未发现")

        # 混淆函数检测
        obfuscation_found = any(re.search(rf"\b{func}\b", self.content) for func in self.OBFUSCATION_PATTERNS)
        report.append("\n## 混淆函数")
        report.append("发现：" + ", ".join(func for func in self.OBFUSCATION_PATTERNS if func in self.content) if obfuscation_found else "未发现")

        # 嵌套调用检测
        eval_b64 = bool(re.search(r"eval\s*\(\s*base64_decode", self.content))
        create_func = bool(re.search(r"create_function\s*\(", self.content))
        report.append("\n## 嵌套/动态调用")
        if eval_b64:
            report.append("- 存在 `eval(base64_decode(...))`")
            decoded_blocks = self.extract_eval_base64_blocks()
            for i, block in enumerate(decoded_blocks[:2]):
                report.append(f"### 段 {i+1} 解码：\n```php\n{block[:300]}\n```")
        if create_func:
            report.append("- 使用 `create_function`")
        if not (eval_b64 or create_func):
            report.append("- 无")

        # 动态函数名检测
        dynamic_funcs = self.detect_dynamic_function_names()
        if dynamic_funcs:
            report.append("\n## ⚙️ 动态生成的函数名")
            for var, func in dynamic_funcs.items():
                report.append(f"- `${var}` -> `{func}`")

        # Preg_replace 执行检测
        executed_code = self.detect_preg_replace_eval()
        if executed_code:
            report.append("\n## 🚨 Preg_replace 执行的代码")
            report.append(f"```php\n{executed_code}\n```")

        # Payload 解码
        decoded_payload = self.decode_payload_chain()
        if decoded_payload:
            report.append("\n## 🔓 解码和解压后的 Payload")
            report.append(f"```php\n{decoded_payload[:300]}\n```")

        # 威胁评分
        score = self.calculate_threat_level()
        report.append(f"\n## 🧾 威胁评分：{score}/10")
        report.append(self.threat_description(score))

        # 添加分类信息
        classification = self.classify()
        report.append(f"\n## 📋 WebShell 分类：{classification}")

        return "\n".join([item for item in report if item is not None])


    def save_report(self, report_text):
        """保存报告到文件"""
        out_path = "./report/"+os.path.basename(self.file_path) + "_report.md"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(report_text)
        return out_path

if __name__ == "__main__":
    # 示例使用
    file_path = r"C:\Users\lowi\Downloads\dataset\webshell\dest\black_0ab432a5e2d8f5b4efffc1d570240bdd.php"
    analyzer = WebShellAnalyzer(file_path)
    report_text = analyzer.analyze()
    report_file = analyzer.save_report(report_text)
    print(f"分析报告已生成：{report_file}")