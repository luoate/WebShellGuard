<script setup lang="ts">
import { reactive, watch, ref } from "vue";
import "vue-json-pretty/lib/styles.css";
import VueJsonPretty from "vue-json-pretty";
import axios from "axios";
import { message } from "@/utils/message";
import { createFormData } from "@pureadmin/utils";
import type { UploadFile, UploadRawFile } from "element-plus";

defineOptions({
  name: "JsonEditor"
});

const dialogVisible = ref(false);
const fileContent = ref("");
const codeContent = ref("");
const fileList = ref<UploadFile[]>([]);
const loading = ref(false);
const error = ref(null);
const inputMode = ref("upload"); // 'upload' or 'code'
let dataStr = '{"tokenSequence":[],"stringSequence":[],"tags":[]}';
const encoder = new TextEncoder();
const beforeUpload = (file: UploadRawFile) => {
  const allowedExtensions = [".php", ".zip"];
  const isAllowed = allowedExtensions.some(ext => file.name.endsWith(ext));

  if (!isAllowed) {
    message("只能上传.php或.zip文件", { type: "error" });
    return false;
  }
  return true;
};

const readFileContent = (file: UploadFile) => {
  return new Promise<string>(resolve => {
    const reader = new FileReader();
    reader.onload = e => resolve(e.target.result as string);
    reader.readAsText(file.raw);
  });
};

const sendCode = async () => {
  try {
    loading.value = true;
    error.value = null;

    let contentToSend = "";

    if (inputMode.value === "upload") {
      if (fileList.value.length === 0) {
        message("请先上传文件", { type: "error" });
        return;
      }
      contentToSend = await readFileContent(fileList.value[0]);
    } else {
      if (!codeContent.value.trim()) {
        message("请输入代码", { type: "error" });
        return;
      }
      contentToSend = codeContent.value;
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
  <el-card shadow="never">
    <el-radio-group v-model="inputMode" class="mb-4">
      <el-radio-button label="upload">上传文件</el-radio-button>
      <el-radio-button label="code">输入代码</el-radio-button>
    </el-radio-group>

    <template v-if="inputMode === 'upload'">
      <el-upload
        v-model:file-list="fileList"
        drag
        :limit="1"
        action="#"
        :auto-upload="false"
        :before-upload="beforeUpload"
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
    </template>
    <template v-else>
      <el-input
        v-model="codeContent"
        type="textarea"
        :rows="5"
        placeholder="请输入代码"
        class="mb-4"
      />
    </template>

    <el-button type="primary" :loading="loading" @click="sendCode">
      发送{{ inputMode === "upload" ? "文件" : "代码" }}
    </el-button>

    <template #header>
      <div class="card-header">
        <span class="font-bold">
          预处理的作用是将代码转化为深度学习模型可以解析的形式
        </span>
      </div>
    </template>
    <el-divider />
    <el-card shadow="never">
      <template #header>
        <div class="text-lg font-bold">预处理结果</div>
      </template>
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
    </el-card>
  </el-card>
</template>

<style lang="scss" scoped>
.el-upload-dragger {
  border: 2px dashed #e5e7eb;
  transition: border-color 0.3s;
  &:hover {
    border-color: #409eff;
  }
}

.el-upload__text {
  margin: 10px 0;
  text-align: center;
  color: #606266;
}

.file-content {
  white-space: pre-wrap;
  word-wrap: break-word;
  max-height: 400px;
  overflow-y: auto;
  background-color: #f5f7fa;
  padding: 12px;
  border-radius: 4px;
  font-family: monospace;
  font-size: 14px;
  line-height: 1.5;
}
</style>
