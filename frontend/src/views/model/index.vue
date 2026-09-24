<script setup lang="ts">
import { ref, onMounted, onUnmounted } from "vue";
import { useRouter } from "vue-router";
import { http } from "@/utils/http";
import * as echarts from "echarts";
import { ElMessage, ElMessageBox } from "element-plus";
import { Edit } from "@element-plus/icons-vue";

defineOptions({
  name: "Model"
});

// 模型参数
const modelParams = ref({
  modelName: "",
  datasetName: "",
  sequenceLength: 8,
  numBatches: 16,
  learningRate: 0.01,
  batchSize: 8,
  epochs: 10,
  optimizer: "adam"
});

// 训练状态
const trainingStatus = ref({
  isTraining: false,
  progress: 0
});

// 保存状态
const isSaving = ref(false);

// 图表数据和训练记录
const chartData = ref({
  loss: [],
  accuracy: []
});

// 训练过程记录
const trainingRecords = ref<
  Array<{
    epoch: number;
    loss: number;
    accuracy: number;
    time: string;
  }>
>([]);

// 图表实例
let chartInstance: echarts.ECharts;

// 初始化图表
const initChart = () => {
  const chartDom = document.getElementById("training-chart");
  if (chartDom) {
    chartInstance = echarts.init(chartDom);
    updateChart();
  }
};

// 更新图表数据
const updateChart = () => {
  const option = {
    title: {
      text: "训练指标",
      left: "center",
      textStyle: {
        color: "#333",
        fontSize: 18,
        fontWeight: "bold"
      }
    },
    tooltip: {
      trigger: "axis",
      axisPointer: {
        type: "cross",
        label: {
          backgroundColor: "#6a7985"
        }
      }
    },
    legend: {
      data: ["Loss", "Accuracy"],
      top: 30,
      textStyle: {
        color: "#666"
      }
    },
    grid: {
      left: "3%",
      right: "4%",
      bottom: "3%",
      containLabel: true,
      backgroundColor: "#f9f9f9",
      borderColor: "#eee",
      show: true,
      borderWidth: 1
    },
    xAxis: {
      type: "category",
      boundaryGap: false,
      data: Array.from(
        { length: chartData.value.loss.length },
        (_, i) => `Epoch ${i + 1}`
      ),
      axisLine: {
        lineStyle: {
          color: "#999"
        }
      }
    },
    yAxis: [
      {
        type: "value",
        name: "Loss",
        position: "left",
        axisLine: {
          lineStyle: {
            color: "#999"
          }
        },
        splitLine: {
          lineStyle: {
            type: "dashed"
          }
        }
      },
      {
        type: "value",
        name: "Accuracy",
        position: "right",
        min: 0,
        max: 1,
        axisLine: {
          lineStyle: {
            color: "#999"
          }
        },
        splitLine: {
          show: false
        }
      }
    ],
    series: [
      {
        name: "Loss",
        type: "line",
        smooth: true,
        lineStyle: {
          width: 3,
          color: "#5470c6"
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            {
              offset: 0,
              color: "rgba(84, 112, 198, 0.5)"
            },
            {
              offset: 1,
              color: "rgba(84, 112, 198, 0.1)"
            }
          ])
        },
        emphasis: {
          focus: "series"
        },
        data: chartData.value.loss
      },
      {
        name: "Accuracy",
        type: "line",
        smooth: true,
        yAxisIndex: 1,
        lineStyle: {
          width: 3,
          color: "#91cc75"
        },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            {
              offset: 0,
              color: "rgba(145, 204, 117, 0.5)"
            },
            {
              offset: 1,
              color: "rgba(145, 204, 117, 0.1)"
            }
          ])
        },
        emphasis: {
          focus: "series"
        },
        data: chartData.value.accuracy
      }
    ],
    animationDuration: 2000
  };
  chartInstance?.setOption(option);
};

const selectedEpoch = ref<number | null>(null);
const savedEpoch = ref(false);
const datasetFile = ref<File | null>(null);

// 下载模型
const downloadModel = async (row: any) => {
  try {
    const response = await fetch(
      `http://127.0.0.1:11451/model/download?modelName=${row.modelName}`,
      {
        method: "GET"
      }
    );

    if (!response.ok) throw new Error("下载请求失败");

    const blob = await response.blob();
    const url = window.URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `model_${row.modelName}.pth`;
    document.body.appendChild(a);
    a.click();
    window.URL.revokeObjectURL(url);
    document.body.removeChild(a);

    message(`模型 ${row.modelName} 下载成功！`, { type: "success" });
  } catch (error) {
    console.error("下载失败:", error);
    message("模型下载失败，请重试！", { type: "error" });
  }
};

// 下载训练集
const downloadTrainDataset = async (row: any) => {
  try {
    // loading.value = true;
    const response = await axios.get(
      "http://127.0.0.1:11451/dataset/download",
      {
        params: {
          dataset: row.trainDataset
        },
        responseType: "blob"
      }
    );

    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement("a");
    link.href = url;
    link.setAttribute("download", `${row.trainDataset}.csv`);
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

// 删除模型
const deleteModel = async (row: any) => {
  try {
    await ElMessageBox.confirm(
      `确认要删除模型 "${row.modelName}" 吗？`,
      "删除确认",
      {
        confirmButtonText: "删除",
        cancelButtonText: "取消",
        type: "warning"
      }
    );

    const response = await fetch(
      `http://127.0.0.1:11451/model/delete?modelName=${encodeURIComponent(row.modelName)}`,
      {
        method: "GET"
      }
    );

    if (!response.ok) throw new Error("删除请求失败");

    const data = await response.json();

    if (data.success && data.deleted > 0) {
      fetchHistory();
      message(`模型 ${row.modelName} 删除成功！`, { type: "success" });
    } else {
      message(`模型 ${row.modelName} 不存在或已删除！`, { type: "warning" });
    }
  } catch (error) {
    if (error !== "cancel") {
      console.error("删除失败:", error);
      message("模型删除失败，请重试！", { type: "error" });
    }
  }
};

const router = useRouter();

// 评估模型
const evaluateModel = async (row: any) => {
  try {
    await router.push({
      path: "/modelEval",
      query: {
        modelName: row.modelName,
        datasetName: row.trainDataset,
        sequenceLength: row.sequenceLength,
        numBatches: row.numBatches,
        learningRate: row.learningRate,
        batchSize: row.batchSize,
        epochs: row.epochs,
        seletedEpoch: row.selectedEpoch,
        optimizer: row.optimizer,
        time: row.time
      }
    });
    // console.log(row.datasetName);
    // console.log("跳转到模型评估页面，模型:", row.modelName);
  } catch (error) {
    console.error("跳转失败:", error);
    // ElMessage.error("跳转到评估页面失败");
    message("跳转到评估页面失败", { type: "error" });
  }
};
// 保存模型
const saveModel = async () => {
  const selectedModel = trainingRecords.value.find(
    item => item.epoch === selectedEpoch.value
  );
  isSaving.value = true;
  const username = useUserStoreHook().username;
  try {
    const response = await fetch("http://127.0.0.1:11451/train/save", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        username: username,
        modelParams: modelParams.value,
        selectedEpoch: selectedEpoch.value,
        accuracy: selectedModel.accuracy,
        loss: selectedModel.loss
      })
    });
    if (!response.ok) {
      message("模型保存请求失败", { type: "error" });
      return;
    }
    message("模型保存成功！", { type: "success" });
    savedEpoch.value = true;
    await fetchHistory();
  } catch (error) {
    console.error("下载失败:", error);
    message("模型保存失败，请重试！", { type: "error" });
  } finally {
    isSaving.value = false;
  }
};

let abortController = null; // 定义在外部，保持引用

// 中止训练
const stopTraining = async () => {
  if (abortController) {
    abortController.abort(); // 取消 fetch（可选）
  }

  try {
    await fetch("http://127.0.0.1:11451/train/stop", {
      method: "POST"
    });
    trainingStatus.value.isTraining = false;
    message("已中止训练", { type: "warning" });
  } catch (error) {
    console.error("中止训练请求失败:", error);
    message("中止训练失败", { type: "error" });
  }
};

// 开始训练
const startTraining1 = async () => {
  if (modelParams.value.modelName === "") {
    message("请输入模型名称！", { type: "error" });
    return;
  }
  savedEpoch.value = false;

  abortController = new AbortController(); // 每次训练前新建一个控制器

  trainingStatus.value.isTraining = true;
  trainingStatus.value.progress = 0;
  chartData.value = { loss: [], accuracy: [] };
  trainingRecords.value = [];

  console.log(modelParams.value);

  try {
    for (let i = 0; i < modelParams.value.epochs; i++) {
      const response = await fetch("http://127.0.0.1:11451/train", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          epoch: i + 1,
          modelParams: modelParams.value
        }),
        signal: abortController.signal // 绑定控制器信号
      });

      // if (!response.ok) throw new Error("训练请求失败");
      if (response.status == 400) {
        message("模型名称重复！", { type: "error" });
        return;
      }

      const data = await response.json();
      const loss = Number(data.loss.toFixed(4));
      const accuracy = Number(data.acc.toFixed(4));

      chartData.value.loss.push(loss);
      chartData.value.accuracy.push(accuracy);
      trainingRecords.value.push({
        epoch: i + 1,
        loss,
        accuracy,
        time: new Date().toLocaleTimeString()
      });

      trainingStatus.value.progress = parseFloat(
        (((i + 1) / modelParams.value.epochs) * 100).toFixed(2)
      );

      updateChart();
    }

    // ElMessage.success("训练完成！");
    message("训练完成！", { type: "success" });
  } catch (error) {
    if (error.name === "AbortError") {
      console.log("训练被中止");
    } else {
      console.error("训练失败:", error);
      // ElMessage.error("训练失败，请重试！");
      message("训练失败，请重试！", { type: "error" });
    }
  } finally {
    trainingStatus.value.isTraining = false;
  }
};

const startTraining = async () => {
  trainingStatus.value.isTraining = true;
  trainingStatus.value.progress = 0;
  chartData.value = { loss: [], accuracy: [] };
  trainingRecords.value = [];
  abortController = new AbortController();

  try {
    for (let i = 0; i < modelParams.value.epochs; i++) {
      // 检查是否中止
      if (abortController.signal.aborted) {
        break;
      }

      await new Promise(resolve => setTimeout(resolve, 1000));

      // 模拟生成训练数据
      const loss = Math.max(
        0.1,
        2 * Math.exp(-i / 3) * (0.9 + Math.random() * 0.2)
      );
      const accuracy = Math.min(
        0.99,
        0.1 + 0.9 * (1 - Math.exp(-i / 2)) * (0.9 + Math.random() * 0.2)
      );

      chartData.value.loss.push(Number(loss.toFixed(4)));
      chartData.value.accuracy.push(Number(accuracy.toFixed(4)));
      trainingRecords.value.push({
        epoch: i + 1,
        loss: Number(loss.toFixed(4)),
        accuracy: Number(accuracy.toFixed(4)),
        time: new Date().toLocaleTimeString()
      });
      trainingStatus.value.progress = parseFloat(
        (((i + 1) / modelParams.value.epochs) * 100).toFixed(2)
      );

      updateChart();
    }

    if (!abortController.signal.aborted) {
      ElMessage.success("训练完成！");
    }
  } catch (error) {
    console.error("训练失败:", error);
    ElMessage.error("训练失败，请重试！");
  } finally {
    trainingStatus.value.isTraining = false;
    abortController = null;
  }
};

// 初始化图表
onMounted(() => {
  initChart();
  fetchDataset();
  fetchHistory();
});

// 组件卸载时销毁图表
onUnmounted(() => {
  chartInstance?.dispose();
  if (abortController) {
    abortController.abort();
  }
});

import axios from "axios";
import { message } from "@/utils/message";
import { useUserStoreHook } from "@/store/modules/user";
const loading = ref(false);
const error = ref(null);
const datasetValue = ref(""); // 存储选中的值
const options = ref([]); // 存储后端返回的选项数据
const fetchDataset = async () => {
  try {
    loading.value = true;
    error.value = null;
    const response = await axios.get("http://127.0.0.1:11451/dataset/getName");

    options.value = response.data;
    // console.log(options);
  } catch (err) {
    error.value = err.message || "获取信息失败";
  } finally {
    loading.value = false;
  }
};

const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);
const fetchHistory = async () => {
  try {
    loading.value = true;
    error.value = null;
    const username = useUserStoreHook().username;
    const response = await axios.get("http://127.0.0.1:11451/train/history", {
      params: {
        username: username,
        page: currentPage.value,
        pageSize: pageSize.value
      }
    });
    // console.log(response);
    tableData.value = (response.data.list || []).map(item => ({
      modelName: item[0],
      trainDataset: item[1],
      learningRate: item[2],
      sequenceLength: item[3],
      numBatches: item[4],
      batchSize: item[5],
      epochs: item[6],
      selectedEpoch: item[7],
      optimizer: item[8],
      accuracy: item[9],
      loss: item[10],
      time: item[11]
    }));
    total.value = response.data.total;
  } catch (err) {
    error.value = err.message || "获取历史记录失败";
  } finally {
    loading.value = false;
  }
};
const tableData = ref([
  {
    modelName: "样例模型",
    trainDataset: "训练集",
    learningRate: 0.01,
    sequenceLength: 8,
    numBatches: 16,
    batchSize: 8,
    epochs: 10,
    selectedEpoch: 7,
    optimizer: "adam",
    accuracy: 0.95,
    loss: 0.12,
    time: "2025-04-14 20:10:00"
  }
]);
const columns = [
  { label: "模型名称", prop: "modelName", align: "center", slot: "modelName" },
  {
    label: "训练集",
    prop: "trainDataset",
    align: "center",
    slot: "trainDataset"
  },
  { label: "学习率", prop: "learningRate", align: "center" },
  { label: "序列长度", prop: "sequenceLength", align: "center" },
  { label: "批次数", prop: "numBatches", align: "center" },
  { label: "批大小", prop: "batchSize", align: "center" },
  { label: "保存/训练轮次", slot: "epochs", prop: "epochs", align: "center" },
  { label: "优化器", prop: "optimizer", align: "center" },
  { label: "准确率", prop: "accuracy", align: "center" },
  { label: "损失值", prop: "loss", align: "center" },
  { label: "时间", prop: "time", width: 160, align: "center" },
  {
    label: "操作",
    slot: "operation",
    width: "180",
    align: "center"
  }
  // sequenceLength: 8,
  // numBatches: 16,
  // learningRate: 0.01,
  // batchSize: 8,
  // epochs: 10,
  // optimizer: "adam",
  // dataset: "train",
  // modelName: ""
  // {
  //   label: "检测结果",
  //   prop: "tag",
  //   slot: "tag"
  // },
  // { label: "上传时间", prop: "time" },
];
const editingRow = ref(null);
const originalModelName = ref("");
function startEditing(row: any) {
  editingRow.value = row;
  originalModelName.value = row.modelName;
}

function stopEditing() {
  if (!editingRow.value) return;

  const row = editingRow.value;

  if (row.modelName !== row._originalModelName) {
    console.log("模型名称已修改：", row.modelName);

    // 调用后端更新，例如：
    updateModelName(row);
  }
  editingRow.value = null;
}

const updateModelName = async (row: any) => {
  try {
    const response = await fetch(
      `http://127.0.0.1:11451/model/update?newModelName=${encodeURIComponent(row.modelName)}&modelName=${encodeURIComponent(originalModelName.value)}`,
      {
        method: "GET"
      }
    );

    if (!response.ok) throw new Error("重命名请求失败");

    const data = await response.json();

    if (data.success && data.updated > 0) {
      fetchHistory();
      message("模型重命名成功！", { type: "success" });
    } else {
      message(`模型 ${row.modelName} 不存在或已删除！`, { type: "warning" });
    }
  } catch (error) {
    if (error !== "cancel") {
      console.error("重命名失败:", error);
      message("重命名失败，请重试！", { type: "error" });
    }
  }
};
</script>

<template>
  <div>
    <el-row :gutter="20">
      <el-col :span="8">
        <el-card class="params-card">
          <template #header>
            <div class="card-header text-lg font-bold">
              <span>模型参数</span>
            </div>
          </template>

          <el-form :model="modelParams" label-width="120px">
            <el-form-item label="模型名称" :rules="[{ required: true }]">
              <el-input
                v-model="modelParams.modelName"
                placeholder="请输入模型名称"
              />
            </el-form-item>

            <el-form-item label="训练数据集" :rules="[{ required: true }]">
              <el-select
                v-model="modelParams.datasetName"
                placeholder="请选择数据集"
              >
                <el-option
                  v-for="item in options"
                  :key="item.name"
                  :label="item.name"
                  :value="item.name"
              /></el-select>
            </el-form-item>

            <el-form-item label="学习率">
              <el-slider
                v-model="modelParams.learningRate"
                :min="0.0001"
                :max="0.05"
                :step="0.0001"
                show-input
              />
            </el-form-item>

            <el-form-item label="序列长度">
              <el-input-number
                v-model="modelParams.sequenceLength"
                :min="1"
                :max="512"
                :step="2"
              />
            </el-form-item>

            <el-form-item label="批次数">
              <el-input-number
                v-model="modelParams.numBatches"
                :min="1"
                :max="512"
                :step="2"
              />
            </el-form-item>

            <el-form-item label="批大小">
              <el-input-number
                v-model="modelParams.batchSize"
                :min="1"
                :max="128"
              />
            </el-form-item>

            <!-- <el-form-item label="Wokers Number">
              <el-input-number
                v-model="modelParams.numWokers"
                :min="1"
                :max="512"
                :step="2"
              />
            </el-form-item> -->

            <el-form-item label="训练轮次">
              <el-input-number
                v-model="modelParams.epochs"
                :min="1"
                :max="100"
              />
            </el-form-item>

            <el-form-item label="优化器">
              <el-select v-model="modelParams.optimizer">
                <el-option label="Adam" value="adam" />
                <el-option label="SGD" value="sgd" />
                <el-option label="RMSprop" value="rmsprop" />
              </el-select>
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                :loading="trainingStatus.isTraining"
                @click="startTraining1"
              >
                开始训练
              </el-button>
              <el-button
                type="danger"
                :disabled="!trainingStatus.isTraining"
                style="margin-left: 10px"
                @click="stopTraining"
              >
                中止训练
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <el-col :span="16">
        <el-card>
          <template #header>
            <div class="card-header">
              <span class="text-lg font-bold">训练过程</span>
              <el-progress
                :percentage="trainingStatus.progress"
                :status="trainingStatus.isTraining ? null : 'success'"
                style="width: 300px; margin-left: 20px"
              />
            </div>
          </template>

          <div id="training-chart" style="width: 100%; height: 420px" />

          <div>
            <el-select
              v-model="selectedEpoch"
              placeholder="请选择要操作的epoch"
              style="width: 80%"
              :disabled="trainingStatus.isTraining"
            >
              <el-option
                v-for="record in trainingRecords"
                :key="record.epoch"
                :label="`Epoch ${record.epoch} (Loss: ${record.loss}, Accuracy: ${record.accuracy})`"
                :value="record.epoch"
              />
            </el-select>

            <el-button
              type="primary"
              style="margin-left: 40px"
              :loading="isSaving"
              :disabled="
                trainingStatus.isTraining ||
                trainingRecords.length === 0 ||
                !selectedEpoch ||
                savedEpoch
              "
              @click="saveModel"
            >
              保存模型
            </el-button>
          </div>
        </el-card>
      </el-col>
    </el-row>
    <el-card class="mt-4">
      <template #header>
        <div class="text-lg font-bold">
          <span>训练记录</span>
        </div>
      </template>
      <pure-table
        ref="tableRef"
        v-loading="loading"
        row-key="time"
        :data="tableData"
        :columns="columns"
      >
        <template #modelName="{ row }">
          <template v-if="editingRow === row">
            <el-input
              v-model="row.modelName"
              size="small"
              style="width: 90px"
              @blur="stopEditing"
              @keyup.enter="stopEditing"
            />
          </template>
          <template v-else>
            <span
              class="link"
              :title="`下载模型：${row.modelName}`"
              @click="downloadModel(row)"
            >
              {{ row.modelName }}
            </span>
            <el-icon
              class="ml-2 cursor-pointer"
              title="修改模型名称"
              @click.stop="startEditing(row)"
            >
              <Edit />
            </el-icon>
          </template>
        </template>

        <template #trainDataset="{ row }">
          <span
            class="link"
            :title="`下载数据集：${row.trainDataset}`"
            @click="downloadTrainDataset(row)"
            >{{ row.trainDataset }}</span
          >
        </template>
        <template #epochs="{ row }">
          {{ row.selectedEpoch }}/{{ row.epochs }}
        </template>
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
        <template #operation="{ row }">
          <el-button type="primary" size="small" @click="evaluateModel(row)">
            评估模型
          </el-button>
          <el-button type="danger" size="small" @click="deleteModel(row)">
            删除模型
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
    </el-card>
  </div>
</template>

<style scoped>
.model-container {
  padding: 20px;
}

.params-card {
  height: 100%;
}
.el-input {
  font-size: 13px;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.upload-demo {
  display: flex;
  align-items: center;
}
.pagination-container {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
  @media (max-width: 768px) {
    justify-content: center;
  }
}
.link {
  color: #409eff;
  cursor: pointer;
  text-decoration: underline;
}
</style>
