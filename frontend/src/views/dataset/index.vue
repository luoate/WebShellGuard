<script setup lang="ts">
import { ref, onMounted } from "vue";
import axios from "axios";
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
  DocumentChecked,
  Files,
  Failed,
  Checked,
  DocumentAdd,
  Download,
  Delete
} from "@element-plus/icons-vue";
import { marked } from "marked";
import { ElMessage, UploadFile } from "element-plus";
import { message } from "@/utils/message";
defineOptions({
  name: "Dataset"
});

// 一定要先`extend`
dayjs.extend(utc);
dayjs.extend(timezone);

const dialogVisible = ref(false);
const dialogVisible2 = ref(false);
const dialogVisible3 = ref(false);
const datasetForm = ref({
  name: "",
  type: "blank",
  baseDataset: ""
});
const fileContent = ref("");
let reportContent = "";
const fileContentHightLight = ref("");
const fileName = ref("");
let fileDetail = "";
// const tableData = ref([]);
const columns = [
  { label: "文件名", prop: "filename", slot: "filename" },
  { label: "Hash", prop: "hash" },
  {
    label: "反馈内容",
    prop: "tag",
    slot: "tag"
  },
  { label: "反馈时间", prop: "feedbackTime" },
  {
    label: "操作",
    width: "180",
    fixed: "right",
    slot: "operation",
    align: "center"
  }
];
const tableData = ref([
  {
    filename: "文件名",
    hash: "sjkahfkjsahkjfhkjashfkjashfhas",
    tag: "恶意",
    time: "2025-04-14 20:10:00"
  }
]);
const loading = ref(false);
const error = ref(null);
const currentPage = ref(1);
const pageSize = ref(5);
const total = ref(0);
const sampleTotal = ref(0);
const blackNum = ref(0);
const whiteNum = ref(0);

const datasetValue = ref(""); // 存储选中的值
const options = ref([]); // 存储后端返回的选项数据

const fetchInfo = async () => {
  try {
    loading.value = true;
    // error.value = null;
    const response = await axios.get("http://127.0.0.1:11451/dataset/getName");

    options.value = response.data;
    // console.log(options);
  } catch (err) {
    error.value = err.message || "获取信息失败";
    message("获取信息失败", { type: "error" });
  } finally {
    loading.value = false;
  }
};
const fetchHistory = async () => {
  try {
    loading.value = true;
    error.value = null;
    const response = await axios.get(
      "http://127.0.0.1:11451/feedback/history",
      {
        params: {
          page: currentPage.value,
          pageSize: pageSize.value
        }
      }
    );
    // console.log(response);
    tableData.value = (response.data.list || []).map(item => ({
      filename: item[0],
      hash: item[1],
      time: dayjs(item[2]).tz("GMT").format("YYYY/MM/DD HH:mm:ss"),
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
      id: item[13],
      feedbackTime: item[14]
    }));
    total.value = response.data.total;
  } catch (err) {
    error.value = err.message || "获取历史记录失败";
  } finally {
    loading.value = false;
  }
};
// 根据选中的数据集更新页面
const updateDataset = async () => {
  await fetchInfo();
  // 找到选中的数据集并更新 dataset
  const selectedDataset = options.value.find(
    item => item.name === datasetValue.value
  );
  if (selectedDataset) {
    whiteNum.value = selectedDataset.white_num; // 更新白数据
    blackNum.value = selectedDataset.black_num; // 更新黑数据
    sampleTotal.value = whiteNum.value + blackNum.value;
  } else {
    whiteNum.value = 0; // 更新白数据
    blackNum.value = 0; // 更新黑数据
    sampleTotal.value = 0;
  }
};
// todo
const feedback = async (row: any) => {
  try {
    loading.value = true;
    // error.value = null;
    const username = useUserStoreHook().username;
    const response = await axios.get("http://127.0.0.1:11451/history", {
      params: {
        user: username,
        page: currentPage.value,
        pageSize: pageSize.value
      }
    });
  } catch (err) {
    error.value = err.message || "获取历史记录失败";
    message("获取历史记录失败", { type: "error" });
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
  fetchInfo();
  fetchHistory();
});

// onActivated(() => {
//   // Refresh data when component is reactivated
//   fetchHistory();
// });
const username = useUserStoreHook().username;
const sampleType = ref("normal"); // Default to white sample
const fileList = ref<any[]>([]); // File list as an array
const uploadSample = async () => {
  if (datasetValue.value.length === 0) {
    alert("请选择数据集");
    return;
  }
  if (fileList.value.length === 0) {
    alert("请上传文件");
    return;
  }

  const formData = new FormData();
  formData.append("sampleType", sampleType.value);
  formData.append("file", fileList.value[0].raw);
  formData.append("dataset", datasetValue.value);
  formData.append("username", username);

  loading.value = true;

  try {
    const response = await axios.post(
      "http://127.0.0.1:11451/dataset/upload",
      formData,
      {
        headers: {
          "Content-Type": "multipart/form-data"
        }
      }
    );

    if (response.status == 200) {
      message("文件上成功", { type: "success" });

      updateDataset();
    } else {
      message("文件上失败", { type: "error" });
    }
  } catch (error) {
    message("上传过程中出错", { type: "error" });
    console.error(error);
  } finally {
    loading.value = false;
    fileList.value = [];
  }
};
const deleteDataset = async () => {
  try {
    if (datasetValue.value == "") {
      message("请选择数据集", { type: "error" });
      return;
    }

    loading.value = true;
    const response = await axios.post("http://127.0.0.1:11451/dataset/delete", {
      name: datasetValue.value
    });

    if (response.status === 200) {
      message("数据集删除成功", { type: "success" });
    }

    dialogVisible3.value = false;
    datasetValue.value = ""; // Clear dataset selection after deletion
    // Refresh dataset list after deletion
    fetchInfo();
    updateDataset();
  } catch (err) {
    // error.value = err.message || "删除数据集失败";
    message("数据集删除失败", { type: "error" });
  } finally {
    loading.value = false;
  }
};

const createDataset = async () => {
  try {
    if (datasetForm.value.name == "") {
      message("请输入数据集名称", { type: "error" });
      return;
    } else if (
      datasetForm.value.baseDataset == "existing" &&
      datasetValue.value == ""
    ) {
      message("请选择数据集", { type: "error" });
      return;
    }

    loading.value = true;

    const selectedDataset = options.value.find(
      item => item.name === datasetValue.value
    );
    const response = await axios.post("http://127.0.0.1:11451/dataset/create", {
      user: username,
      name: datasetForm.value.name,
      type: datasetForm.value.type,
      baseDataset:
        datasetForm.value.type === "existing" ? datasetValue.value : null,
      whiteNum:
        datasetForm.value.type === "existing" ? selectedDataset.white_num : 0,
      blackNum:
        datasetForm.value.type === "existing" ? selectedDataset.black_num : 0
    });

    if (response.status === 200) {
      message("数据集创建成功", { type: "success" });
    }
    // else if (response.status === 400) {
    //   console.log(123);
    //   message("数据库名称重复！", { type: "error" });
    //   return;
    // }

    dialogVisible3.value = false;
    // Refresh dataset list after creation
    fetchInfo();
    datasetValue.value = datasetForm.value.name;
    updateDataset();
  } catch (err) {
    // console.log(321);
    // error.value = err.message || "创建数据集失败";
    message("数据库名称重复！", { type: "error" });
  } finally {
    loading.value = false;
  }
};
const downloadDataset = async () => {
  if (!datasetValue.value) {
    message("请先选择数据集", { type: "warning" });
    return;
  }

  try {
    loading.value = true;
    const response = await axios.get(
      "http://127.0.0.1:11451/dataset/download",
      {
        params: {
          dataset: datasetValue.value
        },
        responseType: "blob"
      }
    );

    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `${datasetValue.value}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(url);

    message("数据集下载成功", { type: "success" });
  } catch (error) {
    message("数据集下载失败", { type: "error" });
    console.error(error);
  } finally {
    loading.value = false;
  }
};
</script>

<template>
  <div>
    <div>
      <el-card shadow="never">
        <template #header>
          <div class="flex justify-between">
            <div>
              <span class="text-lg font-bold">数据集选择</span>
              <el-select
                v-model="datasetValue"
                style="width: 500px; margin-left: 30px"
                @change="updateDataset"
              >
                <el-option
                  v-for="item in options"
                  :key="item.name"
                  :label="item.name"
                  :value="item.name"
              /></el-select>
            </div>

            <div class="flex gap-2">
              <el-button type="primary" @click="dialogVisible3 = true">
                <el-icon class="mr-1"><DocumentAdd /></el-icon>新建数据集
              </el-button>
              <el-button type="danger" @click="deleteDataset">
                <el-icon class="mr-1"><Delete /></el-icon>删除数据集
              </el-button>
              <el-button type="success" @click="downloadDataset">
                <el-icon class="mr-1"><Download /></el-icon>下载数据集
              </el-button>
            </div>
          </div>
        </template>
        <div class="card-container">
          <el-card shadow="always" class="stat-card">
            <div class="card-content">
              <el-icon class="stat-icon"><Files /></el-icon>
              <p class="stat-value">样本总数：{{ sampleTotal }}</p>
            </div>
          </el-card>
          <el-card shadow="always" class="stat-card">
            <div class="card-content">
              <el-icon class="warning-icon"><Failed /></el-icon>
              <p class="stat-value">黑样本: {{ blackNum }}</p>
            </div>
          </el-card>
          <el-card shadow="always" class="stat-card">
            <div class="card-content">
              <el-icon class="check-icon"><Checked /></el-icon>
              <p class="stat-value">白样本: {{ whiteNum }}</p>
            </div>
          </el-card>
        </div>
      </el-card>
    </div>

    <el-card shadow="never" class="mt-4">
      <template #header>
        <div class="flex justify-between">
          <div class="text-lg font-bold">上传样本</div>
        </div>
      </template>
      <div class="mb-4" style="display: flex">
        <span class="mr-4">样本类型：</span>
        <el-radio-group v-model="sampleType">
          <el-radio value="normal">白样本</el-radio>
          <el-radio value="webshell">黑样本</el-radio>
        </el-radio-group>
        <el-button
          type="primary"
          :loading="loading"
          style="margin-left: 50px"
          @click="uploadSample"
        >
          <el-icon class="mr-1"><Upload /></el-icon>上传样本
        </el-button>
      </div>
      <el-upload
        v-model:file-list="fileList"
        drag
        :limit="1"
        action="#"
        :auto-upload="false"
        class="mb-4"
      >
        <div class="el-upload__text">
          <IconifyIconOffline
            icon="ri:upload-2-line"
            width="26"
            class="m-auto mb-2"
          />
          点击或拖拽上传.php或.zip文件
        </div>
      </el-upload>
    </el-card>
    <el-card shadow="never" class="mt-4">
      <template #header>
        <div class="text-lg font-bold">反馈记录</div>
      </template>
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
          <el-tag v-if="row.tag === '恶意'" type="warning" disable-transitions>
            误报
          </el-tag>
          <el-tag v-else type="danger" disable-transitions> 漏报 </el-tag>
        </template>
        <template #operation="{ row }">
          <el-button
            type="primary"
            size="small"
            style="margin-left: 8px"
            @click="showFileDetails(row)"
          >
            查看报告
          </el-button>
        </template>
      </pure-table>
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[5, 10, 20, 50, 100]"
          :total="total"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="fetchInfo"
          @size-change="fetchInfo"
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
        <!-- <MarkdownRenderer :content="markdownText" /> -->
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
      <el-dialog v-model="dialogVisible3" title="新建数据集" width="30%">
        <el-form :model="datasetForm" label-width="120px">
          <el-form-item label="数据集名称" :rules="[{ required: true }]">
            <el-input
              v-model="datasetForm.name"
              placeholder="请输入数据集名称"
            />
          </el-form-item>
          <el-form-item label="创建方式">
            <el-radio-group v-model="datasetForm.type">
              <el-radio value="blank">新建空白数据集</el-radio>
              <el-radio value="existing">基于现有数据集</el-radio>
            </el-radio-group>
          </el-form-item>
          <el-form-item
            v-if="datasetForm.type === 'existing'"
            label="选择数据集"
          >
            <el-select
              v-model="datasetValue"
              style="width: 100%"
              @change="updateDataset"
            >
              <el-option
                v-for="item in options"
                :key="item.name"
                :label="item.name"
                :value="item.name"
            /></el-select>
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="dialogVisible3 = false">取消</el-button>
          <el-button type="primary" @click="createDataset">确认</el-button>
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
