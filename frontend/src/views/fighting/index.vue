<script setup lang="ts">
import { ref } from "vue";
import { http } from "@/utils/http";

defineOptions({
  name: "Fighting"
});

// 定义一个响应式变量用于存储请求的数据
const data = ref<string>("");

// 定义请求函数
const textRequest = async () => {
  try {
    const response = await http.request<string>("get", "/api/"); // 指定返回类型为 string
    data.value = response;
  } catch (error) {
    console.error("请求失败：", error);
  }
};
</script>

<template>
  <div>
    <h1>加油</h1>
    <el-button @click="textRequest">获取内容</el-button>
    <p>请求返回内容：{{ data }}</p>
  </div>
</template>
