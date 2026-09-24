from jsonlines import Reader
import re

data_file = 'C:\\Users\\lowi\\Downloads\\php\\php\\final\\jsonl\\train\\php_train_9.jsonl'
des_file = 'C:\\Users\\lowi\\Downloads\\php\\php\\final\\jsonl\\train\\train\\9_{}.php'

# 匹配修饰符的正则表达式
match_str = r'^(abstract\s*)?(final\s*)?(final\s*)?((public|protected|private)\s*)?(static\s*)?'


# 检查并补全大括号的函数
def complete_braces(code):
    # 统计大括号数量
    open_braces = code.count('{')
    close_braces = code.count('}')

    # 如果左大括号多于右大括号，补充右大括号
    if open_braces > close_braces:
        code += '\n' + '}' * (open_braces - close_braces)

    return code


# 清理并格式化代码
def code_pre(outstring):
    # 去除修饰符
    m = re.compile(match_str, re.S)
    while True:
        new_outstring = re.sub(m, '', outstring)
        if new_outstring == outstring:  # 如果没有变化，停止循环
            break
        outstring = new_outstring

    # 补全大括号
    outstring = complete_braces(outstring)

    # 添加 PHP 起始和结束标签
    outtmp = '<?php\n' + outstring + '\n?>'
    return outtmp


if __name__ == '__main__':
    fp = open(data_file, 'r', encoding='utf-8')
    reader = Reader(fp)

    for i, item in enumerate(reader):
        phpcode = code_pre(item['original_string'])
        with open(des_file.format(i), 'w', encoding='utf-8') as fp_out:
            fp_out.write(phpcode)
        print('done:{}'.format(i))
