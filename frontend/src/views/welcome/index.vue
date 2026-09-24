<script setup lang="ts">
import { useRouter } from "vue-router";
import {
  Upload,
  Warning,
  DeleteFilled,
  WarningFilled,
  Check,
  DocumentChecked,
  Right
} from "@element-plus/icons-vue";
import { bg, avatar, illustration } from "./static";
import { ReNormalCountTo } from "@/components/ReCountTo";

const router = useRouter();

const goToUpload = () => {
  router.push("/upload");
};

const goToReport = () => {
  router.push("/history");
};

const goToTrain = () => {
  router.push("/model");
};

const goToEvaluate = () => {
  router.push("/modelEval");
};
</script>

<template>
  <div class="welcome-container">
    <div class="welcome-content">
      <avatar class="avatar-content" />
      <h1 class="title animate__animated animate__fadeIn">ShellDetector</h1>
      <p class="subtitle animate__animated animate__fadeIn">
        基于Codebert的webshell文件检测与分析平台
      </p>
      <el-button
        type="primary"
        size="large"
        class="start-btn animate__animated animate__fadeIn animate__delay-1s"
        @click="goToUpload"
      >
        快速开始
        <el-icon class="mr-1"><Right /></el-icon>
      </el-button>
      <div class="features animate__animated animate__fadeIn animate__delay-1s">
        <div class="feature-item" @click="goToUpload">
          <div class="feature-icon">📤</div>
          <span>文件上传检测</span>
        </div>
        <div class="feature-item" @click="goToReport">
          <div class="feature-icon">📝</div>
          <span>检测记录及报告</span>
        </div>
        <div class="feature-item" @click="goToTrain">
          <div class="feature-icon">🧠</div>
          <span>深度模型训练</span>
        </div>
        <div class="feature-item" @click="goToEvaluate">
          <div class="feature-icon">📈</div>
          <span>模型性能评估</span>
        </div>
      </div>

      <div class="stats animate__animated animate__fadeIn animate__delay-1s">
        <div class="stat-item">
          <div class="stat-value">
            <ReNormalCountTo
              :startVal="0"
              :endVal="98.7"
              :duration="4000"
              :decimals="1"
              suffix="%"
            />
          </div>
          <div class="stat-label">检测准确率</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">
            <ReNormalCountTo
              :startVal="0"
              :endVal="0.5"
              :duration="4000"
              :decimals="1"
              suffix="s"
            />
          </div>
          <div class="stat-label">平均响应时间</div>
        </div>
        <div class="stat-item">
          <div class="stat-value">
            <ReNormalCountTo :startVal="0" :endVal="1024" :duration="4000" />
          </div>
          <div class="stat-label">累计检测出</div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.welcome-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: linear-gradient(135deg, #c7deff 0%, #c3cfe2 100%);
  border-radius: 10px; /* 倒角半径，可根据需要调整 */
  padding: 20px; /* 为了让圆角不被外部内容遮挡 */
  box-sizing: border-box;
}

.welcome-content {
  text-align: center;
  max-width: 800px;
  padding: 2rem;
}

.avatar-content {
  width: 100px;
  height: 100px;
  display: block;
  margin: 0 auto;
}

.title {
  font-size: 2.5rem;
  margin-bottom: 1rem;
  color: #333;
}

.subtitle {
  font-size: 1.2rem;
  color: #666;
  margin-bottom: 2rem;
}

/* .start-btn {
  padding: 0.8rem 2rem;
  font-size: 1.1rem;
  margin-bottom: 3rem;
} */
.start-btn {
  padding: 2rem 2.5rem; /* 更大内边距 */
  font-size: 1.9rem; /* 字体更大 */
  border-radius: 8px; /* 圆角稍微柔和些，看起来更大气 */
  align-items: center;
  justify-content: center;
}

.features {
  display: flex;
  justify-content: space-around;
  margin-top: 2rem;
}

.feature-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 1rem;
  transition: all 0.3s ease; /* 添加过渡效果更平滑 */
}

.feature-item:hover {
  background-color: #f0f0f0; /* 悬停时变背景色 */
  transform: scale(1.05); /* 悬停时微微放大 */
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1); /* 添加阴影 */
  cursor: pointer; /* 鼠标样式改为手型 */
  border-radius: 12px; /* 添加圆角 */
}

.feature-icon {
  font-size: 2rem;
  margin-bottom: 0.5rem;
}

.feature-item span {
  font-size: 1rem;
  color: #666;
}

.stats {
  display: flex;
  justify-content: space-around;
  margin-top: 3rem;
  background: rgba(255, 255, 255, 0.8);
  padding: 1.5rem;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 1.5rem;
}

.stat-value {
  font-size: 2rem;
  font-weight: bold;
  color: #409eff;
  margin-bottom: 0.5rem;
}

.stat-label {
  font-size: 1rem;
  color: #666;
}
</style>
