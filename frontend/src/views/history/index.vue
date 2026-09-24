<script setup lang="ts">
import { ref, onMounted } from "vue";
import axios from "axios";
import { columns } from "./data";
import { useUserStoreHook } from "@/store/modules/user";
import dayjs from "dayjs";
import utc from "dayjs/plugin/utc";
import timezone from "dayjs/plugin/timezone";
import hljs from "highlight.js";
import "highlight.js/styles/github.css";
import {
  Upload,
  Warning,
  DeleteFilled,
  WarningFilled,
  Check,
  DocumentChecked
} from "@element-plus/icons-vue";
import { marked } from "marked";
import { ElMessageBox } from "element-plus";

// 一定要先`extend`
dayjs.extend(utc);
dayjs.extend(timezone);

const dialogVisible = ref(false);
const dialogVisible2 = ref(false);
const fileContent = ref("");
let reportContent = "";
const fileContentHightLight = ref("");
const fileName = ref("");
let fileDetail = "";
const tableData = ref([]);
const loading = ref(false);
const error = ref(null);
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);
const webshell = ref(0);
const normal = ref(0);

const fetchHistory = async () => {
  try {
    loading.value = true;
    error.value = null;
    const username = useUserStoreHook().username;
    const response = await axios.get("http://127.0.0.1:11451/history", {
      params: {
        user: username,
        page: currentPage.value,
        pageSize: pageSize.value
      }
    });
    // console.log(response);
    tableData.value = (response.data.list || []).map(item => ({
      filename: item[0],
      hash: item[1],
      // time: dayjs(item[2]).tz("GMT").format("YYYY/MM/DD HH:mm:ss"),
      time: item[2],
      user: item[3],
      tag: item[4],
      content: item[5],
      file_type: item[6],
      tlst_hash: item[7],
      ssdeep_hash: item[8],
      md5_hash: item[9],
      sha1_hash: item[10],
      file_size: item[11],
      report_content: item[12],
      id: item[13]
    }));
    total.value = response.data.total;
    webshell.value = response.data.webshell;
    normal.value = response.data.normal;
  } catch (err) {
    error.value = err.message || "获取历史记录失败";
  } finally {
    loading.value = false;
  }
};
// 反馈按钮
const feedback = async (row: any) => {
  let str = "";
  if (row.tag == "恶意") {
    str = "误报";
  } else {
    str = "漏报";
  }
  ElMessageBox.alert("感谢反馈！", `${str}反馈`, {
    confirmButtonText: "确定",
    type: "success"
  });
  try {
    loading.value = true;
    error.value = null;
    const response = await axios.get("http://127.0.0.1:11451/feedback", {
      params: {
        uploadID: row.id
        // page: currentPage.value,
        // pageSize: pageSize.value
      }
    });
  } catch (err) {
    error.value = err.message || "反馈失败";
  } finally {
    loading.value = false;
  }
};

const openFile = row => {
  // 先高亮处理代码内容
  const highlightedContent = hljs.highlightAuto(row.content).value;

  // 将高亮内容按行拆分
  const highlightedLines = highlightedContent.split("\n");

  // 将每一行前面添加行号
  const contentWithLineNumbers = highlightedLines
    .map((line, index) => {
      return `<span class="line-number">${index + 1}</span> ${line}`;
    })
    .join("\n");

  // 将处理后的内容赋值给 fileContentHightLight
  fileContentHightLight.value = contentWithLineNumbers;
  fileContent.value = row.content;
  fileName.value = row.filename;
  dialogVisible.value = true;
};

const showFileDetails = async row => {
  if (row.tag == "安全") {
    fileDetail = `
    <b>文件名：</b> ${row.filename}<br>
    <b>MD5：</b> ${row.md5_hash}<br>
    <b>SHA-1：</b> ${row.sha1_hash}<br>
    <b>SHA-256：</b> ${row.hash}<br>
    <b>TLST：</b> ${row.tlst_hash}<br>
    <b>SSDEEP：</b> ${row.ssdeep_hash}<br>
    <b>文件类型：</b> ${row.file_type}<br>
    <b>文件大小：</b> ${row.file_size} bytes
  `;
  } else {
    reportContent = row.report_content;
    fileDetail = await marked(reportContent);
    fileName.value = row.hash + ".md";
  }

  dialogVisible2.value = true;
};

const downloadFile = (row: any) => {
  const blob = new Blob([row.content], { type: "text/plain" });
  const link = document.createElement("a");
  link.href = URL.createObjectURL(blob);
  link.download = row.filename;
  link.click();
  URL.revokeObjectURL(link.href);
};

onMounted(() => {
  fetchHistory();
});

// onActivated(() => {
//   // Refresh data when component is reactivated
//   fetchHistory();
// });
</script>

<template>
  <div>
    <div class="card-container">
      <el-card shadow="always" class="stat-card">
        <div class="card-content">
          <el-icon class="stat-icon"><upload /></el-icon>
          <p class="stat-value">检测文件：{{ total }}</p>
        </div>
      </el-card>
      <el-card shadow="always" class="stat-card">
        <div class="card-content">
          <el-icon class="warning-icon"><WarningFilled /></el-icon>
          <p class="stat-value">恶意文件: {{ webshell }}</p>
        </div>
      </el-card>
      <el-card shadow="always" class="stat-card">
        <div class="card-content">
          <el-icon class="check-icon"><DocumentChecked /></el-icon>
          <p class="stat-value">安全文件: {{ normal }}</p>
        </div>
      </el-card>
    </div>
    <el-card shadow="never" class="mt-6">
      <pure-table
        ref="tableRef"
        v-loading="loading"
        row-key="time"
        :data="tableData"
        :columns="columns"
      >
        <template #empty>
          <el-empty
            v-if="!error"
            description="暂无历史记录"
            :image-size="100"
          />
          <el-alert
            v-else
            :title="error"
            type="error"
            show-icon
            :closable="false"
          />
        </template>
        <template #filename="{ row }">
          <span class="filename" @click="openFile(row)">{{
            row.filename
          }}</span>
        </template>
        <template #tag="{ row }">
          <el-tag
            :key="row.tag"
            :type="
              row.tag === '恶意'
                ? 'danger'
                : row.tag === '安全'
                  ? 'success'
                  : 'warning'
            "
            disable-transitions
          >
            {{ row.tag }}
          </el-tag>
        </template>
        <template #operation="{ row }">
          <el-button
            type="primary"
            size="small"
            style="margin-left: 8px"
            @click="showFileDetails(row)"
          >
            查看
          </el-button>
          <!-- 如果 row.tag 是恶意，则显示“误报” -->
          <el-button
            v-if="row.tag === '恶意'"
            type="warning"
            size="small"
            style="margin-left: 8px"
            @click="feedback(row)"
          >
            误报
          </el-button>

          <!-- 如果 row.tag 不是恶意，则显示“漏报” -->
          <el-button
            v-else
            type="danger"
            size="small"
            style="margin-left: 8px"
            @click="feedback(row)"
          >
            漏报
          </el-button>
        </template>
      </pure-table>
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="fetchHistory"
          @size-change="fetchHistory"
        />
      </div>
      <el-dialog v-model="dialogVisible" title="文件内容" width="50%">
        <pre class="file-content"><code v-html="fileContentHightLight" /></pre>
        <template #footer>
          <el-button @click="dialogVisible = false">关闭</el-button>
          <el-button
            type="primary"
            @click="downloadFile({ filename: fileName, content: fileContent })"
          >
            下载
          </el-button>
        </template>
      </el-dialog>
      <el-dialog v-model="dialogVisible2" title="报告详情" width="50%">
        <div class="file-content" v-html="fileDetail" />
        <template #footer>
          <el-button @click="dialogVisible2 = false">关闭</el-button>
          <el-button
            type="primary"
            @click="downloadFile({ filename: fileName, content: fileDetail })"
          >
            下载
          </el-button>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<style lang="scss" scoped>
.card-container {
  display: flex;
  gap: 16px;
  margin-bottom: 16px;
}
.stat-card {
  flex: 1;
  text-align: center;
  padding: 16px;
}
.stat-icon {
  font-size: 40px;
  color: #409eff;
  margin-bottom: 8px;
}
.warning-icon {
  font-size: 40px;
  color: #f85353;
  margin-bottom: 8px;
}
.check-icon {
  font-size: 40px;
  color: #0ce446;
  margin-bottom: 8px;
}
.stat-value {
  font-size: 24px;
  font-weight: bold;
  margin-top: 8px;
}
.filename {
  color: #409eff;
  cursor: pointer;
  text-decoration: underline;
}
.filename:hover {
  color: #66b1ff;
}
.file-content {
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 400px;
  overflow-y: auto;
  // font-family: "宋体", "SimSun", serif;
}

.line-number {
  display: inline-block;
  width: 40px; /* 确保行号宽度一致 */
  margin-right: 10px;
  color: #aaa;
  text-align: right;
  user-select: none;
  padding-right: 10px; /* 给行号添加右边距 */
}

.pagination-container {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
  @media (max-width: 768px) {
    justify-content: center;
  }
}
// body {
//   font-family: "Times New Roman", Times, serif;
// }

// body * {
//   font-family: "宋体", "SimSun", serif;
// }

// body *:lang(en) {
//   font-family: "Times New Roman", Times, serif;
// }
</style>
