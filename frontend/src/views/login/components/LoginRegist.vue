<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount } from "vue";
import Motion from "../utils/motion";
import { message } from "@/utils/message";
import type { FormInstance } from "element-plus";
import { useUserStoreHook } from "@/store/modules/user";
import { useRenderIcon } from "@/components/ReIcon/src/hooks";
import Lock from "@iconify-icons/ri/lock-fill";
import Iphone from "@iconify-icons/ep/iphone";
import User from "@iconify-icons/ri/user-3-fill";
import { getTopMenu, initRouter } from "@/router/utils";
import router from "@/router";
import { storageLocal } from "@pureadmin/utils";
import { usePermissionStoreHook } from "@/store/modules/permission";

const checked = ref(false);
const loading = ref(false);
const ruleForm = reactive({
  username: "",
  password: "",
  repeatPassword: ""
});
const ruleFormRef = ref<FormInstance>();
const repeatPasswordRule = [
  {
    validator: (rule, value, callback) => {
      if (value === "") {
        callback(new Error("请输入确认密码"));
      } else if (ruleForm.password !== value) {
        callback(new Error("两次密码不一致！"));
      } else {
        callback();
      }
    },
    trigger: "blur"
  }
];

/** 密码正则（密码格式应为6-18位数字、字母、符号的任意两种组合） */
const REGEXP_PWD =
  /^(?![0-9]+$)(?![a-z]+$)(?![A-Z]+$)(?!([^(0-9a-zA-Z)]|[()])+$)(?!^.*[\u4E00-\u9FA5].*$)([^(0-9a-zA-Z)]|[()]|[a-z]|[A-Z]|[0-9]){6,18}$/;

const passwordRule = [
  {
    validator: (rule, value, callback) => {
      if (value === "") {
        callback(new Error("请输入密码"));
      } else if (!REGEXP_PWD.test(value)) {
        callback(new Error("密码格式应为6-18位数字、字母、符号的任意两种组合"));
      } else {
        callback();
      }
    },
    trigger: "blur"
  }
];

function onBack() {
  useUserStoreHook().SET_CURRENTPAGE(0);
}

function onChange() {
  useUserStoreHook()
    .loginByUsername({
      username: ruleForm.username,
      password: ruleForm.username
    })
    .then(res => {
      if (res.success) {
        storageLocal().removeItem("async-routes");
        usePermissionStoreHook().clearAllCachePage();
        initRouter();
      }
    });
  window.location.reload();
}

const onUpdate = async (formEl: FormInstance | undefined) => {
  loading.value = true;
  if (!formEl) return;
  await formEl.validate(valid => {
    if (valid) {
      loading.value = true;
      useUserStoreHook()
        .registerByUsername({
          username: ruleForm.username,
          password: ruleForm.password
        })
        .then(async res => {
          if (res.success) {
            // 获取后端路由
            await initRouter().then(() => {
              router.push(getTopMenu(true).path).then(() => {
                message("注册成功", { type: "success" });
                onChange();
              });
            });
          } else {
            message("重复用户名", { type: "error" });
          }
        })
        .finally(() => (loading.value = false));
    } else {
      loading.value = false;
    }
  });
};
function onkeypress({ code }: KeyboardEvent) {
  if (["Enter", "NumpadEnter"].includes(code)) {
    onUpdate(ruleFormRef.value);
  }
}

onMounted(() => {
  window.document.addEventListener("keypress", onkeypress);
});

onBeforeUnmount(() => {
  window.document.removeEventListener("keypress", onkeypress);
});
</script>

<template>
  <el-form ref="ruleFormRef" :model="ruleForm" size="large">
    <Motion>
      <el-form-item
        :rules="[
          {
            required: true,
            message: '请输入用户名',
            trigger: 'blur'
          }
        ]"
        prop="username"
      >
        <el-input
          v-model="ruleForm.username"
          clearable
          placeholder="用户名"
          :prefix-icon="useRenderIcon(User)"
        />
      </el-form-item>
    </Motion>

    <Motion :delay="200">
      <el-form-item :rules="passwordRule" prop="password">
        <el-input
          v-model="ruleForm.password"
          clearable
          show-password
          placeholder="密码"
          :prefix-icon="useRenderIcon(Lock)"
        />
      </el-form-item>
    </Motion>

    <Motion :delay="250">
      <el-form-item :rules="repeatPasswordRule" prop="repeatPassword">
        <el-input
          v-model="ruleForm.repeatPassword"
          clearable
          show-password
          placeholder="确认密码"
          :prefix-icon="useRenderIcon(Lock)"
        />
      </el-form-item>
    </Motion>

    <Motion :delay="350">
      <el-form-item>
        <el-button
          class="w-full"
          size="default"
          type="primary"
          :loading="loading"
          @click="onUpdate(ruleFormRef)"
        >
          确定
        </el-button>
      </el-form-item>
    </Motion>

    <Motion :delay="400">
      <el-form-item>
        <el-button class="w-full" size="default" @click="onBack">
          返回
        </el-button>
      </el-form-item>
    </Motion>
  </el-form>
</template>
