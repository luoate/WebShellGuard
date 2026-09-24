<script setup lang="ts">
import { onMounted, reactive, ref } from "vue";
import { message } from "@/utils/message";
import { type UserInfo } from "@/api/user";
import type { FormInstance, FormRules } from "element-plus";
import ReCropperPreview from "@/components/ReCropperPreview";
import { createFormData, deviceDetection } from "@pureadmin/utils";
import uploadLine from "@iconify-icons/ri/upload-line";
import { http } from "@/utils/http";
import axios from "axios";
import { useUserStoreHook } from "@/store/modules/user";

defineOptions({
  name: "Account"
});

const imgSrc = ref("");
const cropperBlob = ref();
const cropRef = ref();
const uploadRef = ref();
const isShow = ref(false);
const userInfoFormRef = ref<FormInstance>();
const username = useUserStoreHook().username;

const userInfos = reactive({
  username: "",
  avatar: "",
  role: "",
  email: "",
  phone: "",
  description: ""
});

const rules = reactive<FormRules<UserInfo>>({
  username: [{ required: true, message: "用户名必填", trigger: "blur" }]
});

function queryEmail(queryString, callback) {
  const emailList = [
    { value: "@qq.com" },
    { value: "@126.com" },
    { value: "@163.com" }
  ];
  let results = [];
  let queryList = [];
  emailList.map(item =>
    queryList.push({ value: queryString.split("@")[0] + item.value })
  );
  results = queryString
    ? queryList.filter(
        item =>
          item.value.toLowerCase().indexOf(queryString.toLowerCase()) === 0
      )
    : queryList;
  callback(results);
}

const onChange = uploadFile => {
  const reader = new FileReader();
  reader.onload = e => {
    imgSrc.value = e.target.result as string;
    isShow.value = true;
  };
  reader.readAsDataURL(uploadFile.raw);
};

const handleClose = () => {
  cropRef.value.hidePopover();
  uploadRef.value.clearFiles();
  isShow.value = false;
};

const onCropper = ({ blob }) => (cropperBlob.value = blob);

type Result = {
  success: boolean;
  data: Array<any>;
};

const formUpload = data => {
  return http.request<Result>(
    "post",
    "http://127.0.0.1:11451/upload/avatar",
    { data },
    {
      headers: {
        "Content-Type": "multipart/form-data"
      }
    }
  );
};

const handleSubmitImage = () => {
  const mime = cropperBlob.value.type; // e.g., "image/png"
  const ext = mime.split("/")[1]; // "png"
  const filename = `avatar.${ext}`; // e.g., "avatar.png"

  const formData = createFormData({
    username: username,
    files: new File([cropperBlob.value], filename)
  });

  formUpload(formData)
    .then(({ success, data }) => {
      if (success) {
        message("更新头像成功", { type: "success" });
        handleClose();
      } else {
        message("更新头像失败");
      }
    })
    .catch(error => {
      message(`提交异常 ${error}`, { type: "error" });
    });
};

// 更新信息
const onSubmit = async (formEl: FormInstance) => {
  if (!formEl) return;

  await formEl.validate(async (valid, fields) => {
    if (valid) {
      try {
        const response = await http.request<Result>(
          "post",
          "http://127.0.0.1:11451/account/update",
          { data: userInfos }
        );

        if (response.success) {
          message("更新信息成功", { type: "success" });
          fetchInfo();
        } else {
          message("更新信息失败");
        }
      } catch (error) {
        message(`更新异常 ${error}`, { type: "error" });
      }
    } else {
      console.log("表单校验失败", fields);
    }
  });
};

// getMine().then(res => {
//   Object.assign(userInfos, res.data);
// });

const fetchInfo = async () => {
  try {
    const username = useUserStoreHook().username;
    // console.log(123);
    const response = await axios.get("http://127.0.0.1:11451/account/mine", {
      params: {
        username: username
      }
    });
    Object.assign(userInfos, response.data.data);
    console.log(userInfos);
  } catch (err) {
    message("获取信息失败", { type: "error" });
  } finally {
  }
};
onMounted(() => {
  fetchInfo();
});
</script>

<template>
  <div
    :class="[
      'min-w-[180px]',
      deviceDetection() ? 'max-w-[100%]' : 'max-w-[70%]'
    ]"
  >
    <el-card>
      <template #header>
        <div class="text-lg font-bold">
          <span>个人信息</span>
        </div>
      </template>
      <el-form
        ref="userInfoFormRef"
        label-position="top"
        :rules="rules"
        :model="userInfos"
      >
        <el-form-item label="头像">
          <el-avatar
            :size="80"
            :src="`http://localhost:11451/avatar/` + userInfos.avatar"
          />
          <el-upload
            ref="uploadRef"
            accept="image/*"
            action="#"
            :limit="1"
            :auto-upload="false"
            :show-file-list="false"
            :on-change="onChange"
          >
            <el-button plain class="ml-4">
              <IconifyIconOffline :icon="uploadLine" />
              <span class="ml-2">更新头像</span>
            </el-button>
          </el-upload>
        </el-form-item>
        <el-form-item label="用户名" prop="username">
          <el-input v-model="userInfos.username" placeholder="请输入用户名" />
        </el-form-item>
        <el-form-item label="身份" prop="role">
          <el-select
            v-model="userInfos.role"
            placeholder="请选择身份"
            class="w-full"
            disabled
          >
            <el-option label="管理员" value="admin" />
            <el-option label="训练员" value="trainer" />
            <el-option label="普通用户" value="user" />
          </el-select>
        </el-form-item>
        <el-form-item label="邮箱" prop="email">
          <el-autocomplete
            v-model="userInfos.email"
            :fetch-suggestions="queryEmail"
            :trigger-on-focus="false"
            placeholder="请输入邮箱"
            clearable
            class="w-full"
          />
        </el-form-item>
        <el-form-item label="联系电话">
          <el-input
            v-model="userInfos.phone"
            placeholder="请输入联系电话"
            clearable
          />
        </el-form-item>
        <el-form-item label="简介">
          <el-input
            v-model="userInfos.description"
            placeholder="请输入简介"
            type="textarea"
            :autosize="{ minRows: 6, maxRows: 8 }"
            maxlength="56"
            show-word-limit
          />
        </el-form-item>
        <el-button type="primary" @click="onSubmit(userInfoFormRef)">
          更新信息
        </el-button>
      </el-form>
      <el-dialog
        v-model="isShow"
        width="40%"
        title="编辑头像"
        destroy-on-close
        :closeOnClickModal="false"
        :before-close="handleClose"
        :fullscreen="deviceDetection()"
      >
        <ReCropperPreview ref="cropRef" :imgSrc="imgSrc" @cropper="onCropper" />
        <template #footer>
          <div class="dialog-footer">
            <el-button bg text @click="handleClose">取消</el-button>
            <el-button bg text type="primary" @click="handleSubmitImage">
              确定
            </el-button>
          </div>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>
