<script lang="ts" setup>
import { reactive, ref, computed, watch, onMounted } from "vue";
import { useRouter } from "vue-router";
import { message } from "@/utils/message";
import { createFormData, getKeyList, extractFields } from "@pureadmin/utils";
import { useUserStoreHook } from "@/store/modules/user";
import { formUpload } from "@/api/mock";
import type { UploadFile, UploadRawFile } from "element-plus";
import Sortable from "sortablejs";
import dayjs from "dayjs";

import UploadIcon from "@iconify-icons/ri/upload-2-line";
import "vue-json-pretty/lib/styles.css";
import VueJsonPretty from "vue-json-pretty";

import Add from "@iconify-icons/ep/plus";
import Delete from "@iconify-icons/ri/delete-bin-7-line";
import { ElIcon } from "element-plus";
import { View, Download } from "@element-plus/icons-vue";
import axios from "axios";

defineOptions({
  name: "Upload"
});
// 表单相关逻辑
const formRef = ref();
const uploadRef = ref();
const validateForm = reactive({
  fileList: [],
  times: ""
});
const username = useUserStoreHook().username;

const submitForm = async formEl => {
  sendCode();
  if (!formEl) return;

  const valid = await new Promise(resolve => {
    formEl.validate(valid => {
      resolve(valid);
    });
  });

  if (valid) {
    const readFileContent = (file: UploadFile | File) => {
      return new Promise<string>(resolve => {
        const reader = new FileReader();
        reader.onload = e => resolve(e.target.result as string);
        const fileObj = (file as UploadFile).raw || file; // Handle both UploadFile and raw File objects
        reader.readAsText(fileObj as Blob);
      });
    };
    const uploadTime = dayjs().format("YYYY/MM/DD HH:mm:ss");

    const uploadedFiles = validateForm.fileList.map(async file => ({
      filename: file.name,
      hash: "",
      tag: "检测中",
      time: uploadTime,
      content: await readFileContent(file)
    }));

    const formData = createFormData({
      files: validateForm.fileList.map(file => ({ raw: file.raw })),
      time: uploadTime,
      username: username
    });

    uploadedFiles.forEach(async file => addRow(await file));

    try {
      const { success, data } = await formUpload(formData);
      if (success && data) {
        data.forEach((result, index) => {
          tableData.value[
            tableData.value.length - uploadedFiles.length + index
          ].hash = result.hash;
          tableData.value[
            tableData.value.length - uploadedFiles.length + index
          ].tag = result.tag;
        });
        // 更新后重新排序
        tableData.value.sort((a, b) => {
          return new Date(b.time).getTime() - new Date(a.time).getTime();
        });
        message("提交成功", { type: "success" });
        state.deep = 2;
        if (formEl) formEl.resetFields();
      } else {
        message("提交失败");
      }
    } catch (error) {
      if (error.message.includes("timeout")) {
        message("请求超时，请稍后重试", { type: "error" });
      } else {
        message(`提交异常 ${error}`, { type: "error" });
      }
    }
  } else {
    return false;
  }
};

const resetForm = formEl => {
  if (!formEl) return false;
  formEl.resetFields();
  return true;
};

// 快速操作指南
const quickGuide = [
  "选择文件或输入代码进行检测。",
  "点击提交检测按钮，开始分析。",
  "在下方表格中查看检测结果。"
];

// 表格和文件上传相关逻辑
const router = useRouter();
const curOpenImgIndex = ref(0);
const dialogVisible = ref(false);
const preprocessingDialogVisible = ref(false);
const fileContent = ref("");
const inputCode = ref("");
const detectMode = ref("file");
const fileList = ref([]);

const urlList = computed(() => getKeyList(fileList.value, "url"));
const imgInfos = computed(() => extractFields(fileList.value, "name", "size"));

const handleCodeSubmit = async () => {
  sendCode();
  if (!inputCode.value) {
    message("请输入要检测的代码");
    return;
  }

  try {
    fileList.value = [];
    const blob = new Blob([inputCode.value], { type: "text/plain" });
    const fileLikeObject = { raw: blob };
    fileList.value.push(fileLikeObject);
    const time = dayjs().format("YYYY/MM/DD HH:mm:ss");
    const formData = createFormData({
      files: fileList.value.map(file => ({ raw: file.raw })),
      time: time,
      username: useUserStoreHook().username
    });

    const tempData = {
      filename:
        dayjs(time, "YYYY/MM/DD HH:mm:ss").valueOf().toString() + ".php",
      hash: "",
      tag: "检测中",
      time: time,
      content: inputCode.value
    };
    addRow(tempData);

    const { success, data } = await formUpload(formData);
    if (success && data) {
      const index = tableData.value.length - 1;
      tableData.value[index].hash = data[0].hash;
      tableData.value[index].tag = data[0].tag;
      // 更新后重新排序
      tableData.value.sort((a, b) => {
        return new Date(b.time).getTime() - new Date(a.time).getTime();
      });
      message("代码检测完成", { type: "success" });
      state.deep = 2;
    } else {
      message("代码检测失败");
    }
  } catch (error) {
    message(`代码检测异常: ${error.message}`, { type: "error" });
  }
};

const openFile = row => {
  fileContent.value = row.content;
  dialogVisible.value = true;
};

// 表格数据
const tableData = ref([]);
const columns = [
  { label: "文件名", prop: "filename", slot: "filename" },
  { label: "Hash", prop: "hash", slot: "hash" },
  { label: "检测结果", prop: "tag", slot: "tag" },
  { label: "上传时间", prop: "time", sortable: true }
];

const addRow = row => {
  tableData.value.push(row);
};

// 初始化时不进行排序
onMounted(() => {});

const loading = ref(false);
const error = ref(null);
const inputMode = ref("upload"); // 'upload' or 'code'
let dataStr = '{"tokenSequence":[],"stringSequence":[],"tags":[]}';
const encoder = new TextEncoder();

// Move readFileContent to be accessible by all functions
const readFileContent = (file: UploadFile) => {
  return new Promise<string>(resolve => {
    const reader = new FileReader();
    reader.onload = e => resolve(e.target.result as string);
    reader.readAsText(file.raw);
  });
};

const downloadPreprocessingResult = () => {
  if (!state.val) {
    message("没有可下载的预处理结果", { type: "warning" });
    return;
  }

  const blob = new Blob([state.val], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `preprocessing-result-${dayjs().format("YYYYMMDDHHmmss")}.json`;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
};

const viewPreprocessingResult = () => {
  if (!state.val) {
    message("没有可查看的预处理结果", { type: "warning" });
    return;
  }
  preprocessingDialogVisible.value = true;
};

const sendCode = async () => {
  try {
    loading.value = true;
    error.value = null;

    let contentToSend = "";
    if (detectMode.value === "file") {
      if (validateForm.fileList.length === 0) {
        message("请先上传文件", { type: "error" });
        return;
      }
      contentToSend = await readFileContent(validateForm.fileList[0]);
    } else {
      if (!inputCode.value.trim()) {
        message("请输入代码", { type: "error" });
        return;
      }
      contentToSend = inputCode.value;
    }
    const byteArray = new TextEncoder().encode(contentToSend);
    const response = await axios.post(
      "http://127.0.0.1:9090/api/parser",
      byteArray,
      {
        headers: {
          "Content-Type": "application/octet-stream"
        },
        responseType: "text"
      }
    );

    dataStr = response.data;
    try {
      const newData = JSON.parse(response.data);
      state.val = JSON.stringify(newData, null, 2);
    } catch (jsonErr) {
      state.val = response.data;
    }
  } catch (err) {
    error.value = err.message || "发送代码失败";
  } finally {
    loading.value = false;
  }
};

const defaultData = JSON.parse(dataStr);

const state = reactive({
  val: dataStr,
  data: defaultData,
  showLine: true,
  showLineNumber: true,
  showDoubleQuotes: true,
  showLength: true,
  editable: false,
  showIcon: true,
  deep: 1
});

watch(
  () => state.val,
  newVal => {
    try {
      state.data = JSON.parse(newVal);
    } catch (err) {
      // console.log('JSON ERROR');
    }
  }
);

watch(
  () => state.data,
  newVal => {
    try {
      state.val = JSON.stringify(newVal);
    } catch (err) {
      // console.log('JSON ERROR');
    }
  }
);
</script>

<template>
  <div>
    <el-row :gutter="16" class="equal-height">
      <el-col :span="16" class="flex-card">
        <el-card shadow="never" class="flex-1 mb-4">
          <template #header>
            <div class="text-lg font-bold">Webshell检测</div>
          </template>

          <div class="mb-4 mt-4 flex items-center gap-4">
            <!-- <span class="text-gray-600 font-medium">检测模式：</span> -->
            <el-radio-group v-model="detectMode">
              <el-radio-button label="file">文件上传</el-radio-button>
              <el-radio-button label="code">代码输入</el-radio-button>
            </el-radio-group>
          </div>

          <div v-show="detectMode === 'code'" class="mb-6">
            <el-card shadow="never" class="!border-gray-100">
              <template #header>
                <div class="font-bold text-gray-700">代码输入检测</div>
              </template>
              <el-input
                v-model="inputCode"
                type="textarea"
                :rows="10"
                placeholder="请输入要检测的代码"
              />
              <el-divider />
              <el-button type="primary" size="large" @click="handleCodeSubmit">
                提交检测
              </el-button>
            </el-card>
          </div>

          <div v-show="detectMode === 'file'" class="mb-6">
            <el-card shadow="never" class="!border-gray-100">
              <template #header>
                <div class="font-bold">文件上传检测</div>
              </template>
              <el-form ref="formRef" :model="validateForm" label-width="82px">
                <el-form-item
                  label="附件"
                  prop="fileList"
                  :rules="[{ required: true, message: '附件不能为空' }]"
                >
                  <el-upload
                    ref="uploadRef"
                    v-model:file-list="validateForm.fileList"
                    drag
                    :limit="1"
                    action="#"
                    class="w-full max-w-3xl !h-[200px]"
                    :auto-upload="false"
                    accept=".php"
                  >
                    <div class="el-upload__text">
                      <IconifyIconOffline
                        :icon="UploadIcon"
                        width="26"
                        class="m-auto mb-2"
                      />
                      可点击或拖拽上传
                    </div>
                  </el-upload>
                </el-form-item>

                <el-form-item>
                  <el-button
                    type="primary"
                    size="large"
                    @click="submitForm(formRef)"
                  >
                    提交检测
                  </el-button>
                  <el-button size="large" @click="resetForm(formRef)"
                    >清空文件</el-button
                  >
                </el-form-item>
              </el-form>
            </el-card>
          </div>
        </el-card>
      </el-col>

      <el-col :span="8" class="flex-card">
        <el-card shadow="never" class="flex-1 mb-4">
          <template #header>
            <div class="flex justify-between items-center">
              <div class="text-lg font-bold">预处理结果</div>
              <div class="flex gap-2">
                <el-button
                  type="primary"
                  size="small"
                  @click="viewPreprocessingResult"
                >
                  <el-icon class="mr-1"><View /></el-icon>查看
                </el-button>
                <el-button
                  type="success"
                  size="small"
                  @click="downloadPreprocessingResult"
                >
                  <el-icon class="mr-1"><Download /></el-icon>下载
                </el-button>
              </div>
            </div>
          </template>
          <div class="overflow-auto" style="max-height: 450px">
            <vue-json-pretty
              v-model:data="state.data"
              :deep="state.deep"
              :show-double-quotes="state.showDoubleQuotes"
              :show-line="state.showLine"
              :show-length="state.showLength"
              :show-icon="state.showIcon"
              :show-line-number="state.showLineNumber"
              :editable="state.editable"
            />
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-card shadow="never">
      <template #header>
        <div class="text-lg font-bold">检测结果</div>
      </template>
      <pure-table
        ref="tableRef"
        row-key="time"
        :data="tableData"
        :columns="columns"
        class="!border-gray-100"
      >
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
      </pure-table>

      <el-dialog v-model="dialogVisible" title="文件内容" width="70%">
        <pre class="file-content">{{ fileContent }}</pre>
        <template #footer>
          <el-button @click="dialogVisible = false">关闭</el-button>
        </template>
      </el-dialog>
      <el-dialog
        v-model="preprocessingDialogVisible"
        title="文件内容"
        width="70%"
      >
        <pre class="file-content">{{ dataStr }}</pre>
        <template #footer>
          <el-button @click="preprocessingDialogVisible = false"
            >关闭</el-button
          >
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<style lang="scss" scoped>
.card-title {
  font-size: 30px; /* 字体大小 */
  font-weight: bold; /* 字体加粗 */
  text-align: center; /* 居中对齐 */
  color: #333; /* 字体颜色 */
}
.card-subtitle {
  font-size: 15px; /* 字体大小 */
  text-align: center; /* 居中对齐 */
  color: #474747; /* 字体颜色 */
}
:deep(.card-header) {
  display: flex;

  .header-right {
    display: flex;
    flex: auto;
    align-items: center;
    justify-content: flex-end;
    font-size: 14px;
  }
}

:deep(.el-card__header) {
  border-bottom: 1px solid #f0f0f0;
  padding: 16px 20px;
}

:deep(.el-upload-dragger) {
  border: 2px dashed #e5e7eb;
  transition: border-color 0.3s;
}

:deep(.el-upload-dragger:hover) {
  border-color: #409eff;
}

.filename {
  color: var(--el-color-primary);
  cursor: pointer;
  transition: color 0.2s;
}

.file-content {
  background: #f8fafc;
  padding: 12px;
  border-radius: 4px;
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 400px;
  overflow-y: auto;
}
.card-header {
  font-size: 16px;
  font-weight: bold;
}
.el-upload__text {
  margin: 10px 0;
  text-align: center;
  color: #606266;
}
.equal-height {
  display: flex;
  align-items: stretch;
}
.flex-card {
  flex: 1;
  display: flex;
  flex-direction: column;
}
.number-icon {
  display: inline-flex;
  justify-content: center;
  align-items: center;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background-color: #409eff;
  color: white;
  font-size: 16px;
  font-weight: bold;
}
.icon-style {
  font-size: 40px; /* 图标大小 */
  color: #007bff; /* 图标颜色 */
}
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
</style>
