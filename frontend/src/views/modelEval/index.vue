<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from "vue";
import { useRoute } from "vue-router";
import * as echarts from "echarts";
import { ElMessage, ElMessageBox } from "element-plus";
import axios from "axios";
import { message } from "@/utils/message";
import { Back } from "@element-plus/icons-vue";
import { Console } from "console";
import { useUserStoreHook } from "@/store/modules/user";

defineOptions({
  name: "ModelEval"
});

// 分析状态
const analysisStatus = ref({
  isAnalyzing: false,
  progress: 0
});

// 图表实例
let distributionChart: echarts.ECharts;
let metricsChart: echarts.ECharts;
const username = useUserStoreHook().username;

// 性能指标
const performanceMetrics = ref({
  accuracy: 0,
  loss: 0,
  inferenceSpeed: 0,
  throughput: 0,
  recall: 0,
  precision: 0,
  f1: 0,
  testTime: "0000-00-00 00:00:00"
});

// 样本分布数据
const sampleDistribution = ref({
  positive: 0,
  negative: 0
});

// 数据集选项
const datasetOptions = ref([]);
const datasetValue = ref("");

// 模型选项
const modelOptions = ref([]);
const modelValue = ref("");

// 初始化图表
const initCharts = () => {
  const distributionDom = document.getElementById("distribution-chart");
  const metricsDom = document.getElementById("metrics-chart");

  if (distributionDom) {
    distributionChart = echarts.init(distributionDom);
    updateDistributionChart();
  }

  if (metricsDom) {
    metricsChart = echarts.init(metricsDom);
    updateMetricsChart();
  }
};

const updateTwoDistributionChart = () => {
  const dom = document.getElementById("twoDistribution-chart");
  const chart = echarts.init(dom);

  chart.setOption({
    tooltip: {
      trigger: "axis",
      axisPointer: { type: "shadow" }
    },
    legend: {
      data: ["训练集", "测试集"],
      top: "10%"
    },
    grid: {
      top: "20%",
      left: "3%",
      right: "4%",
      bottom: "3%",
      containLabel: true
    },
    xAxis: {
      type: "category",
      data: ["黑样本", "白样本"]
    },
    yAxis: {
      type: "value"
    },
    series: [
      {
        name: "训练集",
        type: "bar",
        data: [120, 280],
        itemStyle: { color: "#5470C6" }
      },
      {
        name: "测试集",
        type: "bar",
        data: [50, 150],
        itemStyle: { color: "#91CC75" }
      }
    ]
  });
};

// 更新样本分布图表
const updateDistributionChart = () => {
  const option = {
    tooltip: {
      trigger: "item"
    },
    legend: {
      orient: "horizontal",
      bottom: 0,
      left: "center"
    },
    series: [
      {
        name: "样本数量",
        type: "pie",
        radius: "50%",
        data: [
          { value: sampleDistribution.value.positive, name: "正样本" },
          { value: sampleDistribution.value.negative, name: "负样本" }
        ],
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: "rgba(0, 0, 0, 0.5)"
          }
        }
      }
    ]
  };
  distributionChart?.setOption(option);
};

// 更新性能指标图表
const updateMetricsChart = () => {
  // 归一化处理数据
  const maxValues = {
    accuracy: 1,
    loss: 5,
    recall: 1,
    precision: 1,
    inferenceSpeed: Math.max(performanceMetrics.value.inferenceSpeed, 100),
    throughput: Math.max(performanceMetrics.value.throughput, 100)
  };

  const normalizedData = [
    (performanceMetrics.value.accuracy / maxValues.accuracy).toFixed(2),
    (performanceMetrics.value.loss / maxValues.loss).toFixed(2),
    (performanceMetrics.value.recall / maxValues.recall).toFixed(2),
    (performanceMetrics.value.precision / maxValues.precision).toFixed(2),
    (
      performanceMetrics.value.inferenceSpeed / maxValues.inferenceSpeed
    ).toFixed(2), // 越小越好
    (performanceMetrics.value.throughput / maxValues.throughput).toFixed(2)
  ];

  const option = {
    tooltip: {
      trigger: "item"
    },
    legend: {
      data: ["指标值"],
      orient: "horizontal",
      top: 0,
      left: "left"
    },
    radar: {
      indicator: [
        { name: "准确率", max: 1 },
        { name: "损失值", max: 1 },
        { name: "召回率", max: 1 },
        { name: "精确率", max: 1 },
        { name: "推理速度", max: 1 },
        { name: "吞吐量", max: 1 }
      ],
      radius: "65%",
      splitNumber: 4,
      axisName: {
        color: "#333"
      },
      splitArea: {
        areaStyle: {
          color: ["rgba(58, 95, 176, 0.1)"]
        }
      },
      axisLine: {
        lineStyle: {
          color: "rgba(58, 95, 176, 0.5)"
        }
      },
      splitLine: {
        lineStyle: {
          color: "rgba(58, 95, 176, 0.5)"
        }
      }
    },
    series: [
      {
        name: "性能指标",
        type: "radar",
        data: [
          {
            value: normalizedData,
            name: "指标值",
            areaStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: "rgba(58, 95, 176, 0.8)" },
                { offset: 1, color: "rgba(58, 95, 176, 0.2)" }
              ])
            },
            lineStyle: {
              width: 2,
              color: "rgb(58, 95, 176)"
            },
            symbolSize: 6,
            label: {
              show: true,
              formatter: function (params) {
                // 确保顺序与radar.indicator中的顺序一致
                const metrics = {
                  准确率: performanceMetrics.value.accuracy.toFixed(2),
                  损失值: performanceMetrics.value.loss.toFixed(2),
                  召回率: performanceMetrics.value.recall.toFixed(2),
                  精确率: performanceMetrics.value.precision.toFixed(2),
                  推理速度: performanceMetrics.value.inferenceSpeed.toFixed(2),
                  吞吐量: (performanceMetrics.value.throughput * 100).toFixed(2)
                };
                return metrics[params.name]; // 使用指示器名称作为键
              }
            }
          }
        ],
        animationDuration: 2000
      }
    ]
  };
  metricsChart?.setOption(option);
};

const loading = ref(false);
// 获取模型和数据集信息
const fetchInfo = async () => {
  try {
    loading.value = true;
    const response = await axios.get("http://127.0.0.1:11451/dataset/getName");
    datasetOptions.value = response.data;
    const response2 = await axios.get("http://127.0.0.1:11451/model/getName");
    modelOptions.value = response2.data;
    // console.log(options);
  } catch (err) {
    message("获取信息失败！", { type: "error" });
  } finally {
    loading.value = false;
  }
};

// 根据选中的数据集更新页面
const updateDataset = () => {
  console.log(123);
  // 找到选中的数据集并更新 dataset
  const selectedDataset = datasetOptions.value.find(
    item => item.name === datasetValue.value
  );
  if (selectedDataset) {
    console.log(3);
    sampleDistribution.value.positive = selectedDataset.white_num; // 更新白数据
    sampleDistribution.value.negative = selectedDataset.black_num; // 更新黑数据
    // total.value = whiteNum.value + blackNum.value;
  }
  updateDistributionChart();
};

// 根据选中的模型更新页面
const updateModel = () => {
  // 找到选中的模型并更新 dataset
  const selectedModel = modelOptions.value.find(
    item => item.model_name === modelValue.value
  );
  if (selectedModel) {
    // console.log("find");
    modelParams.value = {
      modelName: modelValue.value,
      datasetName: selectedModel.dataset_name,
      sequenceLength: selectedModel.sequence_length,
      numBatches: selectedModel.num_batches,
      learningRate: selectedModel.learning_rate,
      batchSize: selectedModel.batch_size,
      epochs: selectedModel.epochs,
      seletedEpoch: selectedModel.selected_epoch,
      optimizer: selectedModel.optimizer,
      trainTime: selectedModel.training_time
    };
  } else {
    modelParams.value = {
      modelName: "null",
      datasetName: "null",
      sequenceLength: 0,
      numBatches: 0,
      learningRate: 0.0,
      batchSize: 0,
      epochs: 0,
      seletedEpoch: 0,
      optimizer: "null",
      trainTime: "0000-00-00 00:00:00"
    };
  }
  // updateMetricsChart();
};

// 执行性能评估
const runEval = async () => {
  if (!datasetValue.value) {
    message("请先选择数据集", { type: "warning" });
    return;
  }

  analysisStatus.value.isAnalyzing = true;
  analysisStatus.value.progress = 0;

  try {
    // 获取性能指标
    const metricsResponse = await fetch(
      `http://127.0.0.1:11451/model/evaluate?model=${modelValue.value}&dataset=${datasetValue.value}`,
      {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username: username,
          modelName: modelValue.value,
          trainDatasetName: modelParams.value.datasetName,
          testDatasetName: datasetValue.value,
          performanceMetrics: performanceMetrics.value
        })
      }
    );
    if (!metricsResponse.ok) throw new Error("测试失败！");
    const result = await metricsResponse.json();
    if (result.data) {
      performanceMetrics.value = {
        accuracy: result.data.accuracy,
        loss: result.data.loss,
        recall: result.data.recall,
        precision: result.data.precision,
        f1: result.data.f1,
        inferenceSpeed: result.data.inference_speed,
        throughput: result.data.throughput,
        testTime: result.data.time
      };
    } else {
      performanceMetrics.value = result;
    }
    analysisStatus.value.progress = 100;
    updateMetricsChart();
    // ElMessage.success("分析完成");
    message("评估完成！", { type: "success" });
  } catch (error) {
    console.error("评估失败:", error);
    message("评估失败！", { type: "error" });
    // ElMessage.error("分析失败");
  } finally {
    analysisStatus.value.isAnalyzing = false;
    await fetchHistory();
  }
};

// 初始化
onMounted(() => {
  initCharts();
  fetchInfo();
  fetchHistory();

  // 设置初始路由参数
  const route = useRoute();
  if (route.query.modelName) {
    // console.log(123);
    modelValue.value = route.query.modelName as string;
  }
  if (route.query.modelName) {
    modelParams.value.modelName = route.query.modelName as string;
  }
  if (route.query.datasetName) {
    // console.log(route.query.datasetName);
    modelParams.value.datasetName = route.query.datasetName as string;
  }
  if (route.query.sequenceLength) {
    modelParams.value.sequenceLength = parseInt(
      route.query.sequenceLength as string
    );
  }
  if (route.query.numBatches) {
    modelParams.value.numBatches = parseInt(route.query.numBatches as string);
  }
  if (route.query.learningRate) {
    modelParams.value.learningRate = parseFloat(
      route.query.learningRate as string
    );
  }
  if (route.query.batchSize) {
    modelParams.value.batchSize = parseInt(route.query.batchSize as string);
  }
  if (route.query.epochs) {
    modelParams.value.epochs = parseInt(route.query.epochs as string);
  }
  if (route.query.seletedEpoch) {
    modelParams.value.seletedEpoch = parseInt(
      route.query.seletedEpoch as string
    );
  }
  if (route.query.optimizer) {
    modelParams.value.optimizer = route.query.optimizer as string;
  }
  if (route.query.time) {
    modelParams.value.trainTime = route.query.time as string;
  }
});

// 监听路由变化
const route = useRoute();
watch(
  () => route.query.model,
  newModel => {
    if (newModel) {
      modelValue.value = newModel as string;
    }
  }
);

// 组件卸载时销毁图表
onUnmounted(() => {
  distributionChart?.dispose();
  metricsChart?.dispose();
});

// 模型参数
const modelParams = ref({
  modelName: "null",
  datasetName: "null",
  sequenceLength: 0,
  numBatches: 0,
  learningRate: 0.0,
  batchSize: 0,
  epochs: 0,
  seletedEpoch: 0,
  optimizer: "null",
  trainTime: "0000-00-00 00:00:00"
});

const tableData = ref([
  {
    modelName: "小测试",
    trainDatasetName: "train1",
    testDatasetName: "test1",
    accuracy: 0.95,
    loss: 0.12,
    inferenceSpeed: 1,
    recall: 0.333,
    precision: 0.666,
    f1: 0.12,
    throughput: 88,
    testTime: "2025-04-14 20:10:00"
  }
]);
const columns = [
  { label: "模型名称", prop: "modelName", align: "center", slot: "modelName" },
  { label: "训练集", prop: "trainDatasetName", align: "center" },
  { label: "测试集", prop: "testDatasetName", align: "center" },
  { label: "准确率", prop: "accuracy", align: "center" },
  { label: "损失值", prop: "loss", align: "center" },
  { label: "推理速度", prop: "inferenceSpeed", align: "center" },
  { label: "召回率", prop: "recall", align: "center" },
  { label: "精确率", prop: "precision", align: "center" },
  { label: "F1", prop: "f1", align: "center" },
  { label: "吞吐量", prop: "throughput", align: "center" },
  { label: "测试时间", prop: "testTime", width: 160, align: "center" },
  {
    label: "操作",
    slot: "operation",
    width: "180",
    align: "center"
  }
];
const currentPage = ref(1);
const pageSize = ref(10);
const total = ref(0);
const error = ref(null);
const fetchHistory = async () => {
  try {
    loading.value = true;
    error.value = null;
    const response = await axios.get(
      "http://127.0.0.1:11451/model/evaluate/history",
      {
        params: {
          username: username,
          page: currentPage.value,
          pageSize: pageSize.value
        }
      }
    );
    // console.log(response.data.list);
    tableData.value = (response.data.list || []).map(item => ({
      modelName: item[0],
      trainDatasetName: item[1],
      testDatasetName: item[2],
      accuracy: item[3],
      loss: item[4],
      inferenceSpeed: item[5],
      recall: item[6],
      precision: item[7],
      f1: item[8],
      throughput: item[9],
      testTime: item[10],
      id: item[11]
    }));
    // console.log(tableData.value);
    //     model_name,
    //     train_dataset_name,
    //     test_dataset_name,
    //     accuracy,
    //     loss,
    //     inference_speed,
    //     recall,
    //     precision_score,
    //     throughput,
    //     test_time
    // FROM model_evaluate
    total.value = response.data.total;
  } catch (err) {
    error.value = err.message || "获取历史记录失败";
  } finally {
    loading.value = false;
  }
};

const viewRusultFlag = ref(false);
const selectedModelName = ref("");
const selectedTrainDatasetName = ref("");
const selectedTestDatasetName = ref("");
const viewResult = async (row: any) => {
  viewRusultFlag.value = true;
  selectedModelName.value = row.modelName;
  // selectedTrainDatasetName.value = row.trainDatasetName;
  selectedTestDatasetName.value = row.testDatasetName;
  // datasetValue.value = selectedTestDatasetName.value;
  updateTwoDistributionChart(); // 更新样本分布
  // updateDataset();
  modelValue.value = row.modelName;
  updateModel(); // 更新模型参数表格
  performanceMetrics.value = {
    accuracy: row.accuracy,
    loss: row.loss,
    recall: row.recall,
    precision: row.precision,
    f1: row.f1,
    inferenceSpeed: row.inferenceSpeed,
    throughput: row.throughput,
    testTime: row.time
  };
  updateMetricsChart(); // 更新雷达图
};
const goBack = async () => {
  viewRusultFlag.value = false;
  modelValue.value = "";
  performanceMetrics.value = {
    accuracy: 0,
    loss: 0,
    recall: 0,
    precision: 0,
    f1: 0,
    inferenceSpeed: 0,
    throughput: 0,
    testTime: "0000-00-00 00:00:00"
  };
  updateModel(); // 更新模型参数表格
  updateMetricsChart(); // 更新雷达图
};
const deleteRow = async (row: any) => {
  try {
    await ElMessageBox.confirm("确认要删除吗？", "删除确认", {
      confirmButtonText: "删除",
      cancelButtonText: "取消",
      type: "warning"
    });

    const response = await fetch(
      `http://127.0.0.1:11451/model/evaluate/delete?id=${encodeURIComponent(row.id)}`,
      {
        method: "GET"
      }
    );

    if (!response.ok) throw new Error("删除请求失败");

    const data = await response.json();

    if (data.success && data.deleted > 0) {
      fetchHistory();
      message(`记录删除成功！`, { type: "success" });
    } else {
      message(`记录不存在或已删除！`, { type: "warning" });
    }
  } catch (error) {
    if (error !== "cancel") {
      console.error("删除失败:", error);
      message("记录删除失败，请重试！", { type: "error" });
    }
  }
};
const depolyModel = async () => {
  try {
    const response = await fetch(
      `http://127.0.0.1:11451/model/deploy?model=${encodeURIComponent(selectedModelName.value)}`,
      {
        method: "GET"
      }
    );

    if (!response.ok) throw new Error("部署请求失败");

    const data = await response.json();

    if (data.success) {
      // fetchHistory();
      message(`部署成功！`, { type: "success" });
    } else {
      message("部署失败", { type: "warning" });
    }
  } catch (error) {
    console.error("部署请求失败", error);
    message("部署请求失败", { type: "error" });
  }
};
</script>

<template>
  <div>
    <el-row :gutter="20">
      <el-col :span="24">
        <el-card>
          <template #header>
            <div class="flex justify-between items-center">
              <div class="text-lg font-bold">
                <el-button v-show="viewRusultFlag" @click="goBack">
                  <el-icon class="mr-1"><Back /></el-icon>返回
                </el-button>
                <span v-show="!viewRusultFlag">模型性能评估</span>
                <span
                  v-show="viewRusultFlag"
                  class="ml-2 font-semibold text-blue-400 bg-gray-100 p-2 rounded-lg"
                >
                  {{ selectedModelName }}
                </span>
                <span v-show="viewRusultFlag">&nbsp;模型评估结果</span>
              </div>

              <el-button
                v-show="viewRusultFlag"
                type="primary"
                @click="depolyModel"
                >部署模型</el-button
              >
            </div>
          </template>

          <el-form
            v-show="!viewRusultFlag"
            :inline="true"
            class="demo-form-inline form-flex"
          >
            <el-form-item label="待测模型">
              <el-select
                v-model="modelValue"
                placeholder="请选择待测试模型"
                class="long-select"
                @change="updateModel"
              >
                <el-option
                  v-for="item in modelOptions"
                  :key="item.model_name"
                  :label="item.model_name"
                  :value="item.model_name"
                />
              </el-select>
            </el-form-item>
            <el-form-item label="测试数据集">
              <el-select
                v-model="datasetValue"
                placeholder="请选择数据集"
                class="long-select"
                @change="updateDataset"
              >
                <el-option
                  v-for="item in datasetOptions"
                  :key="item.name"
                  :label="item.name"
                  :value="item.name"
                />
              </el-select>
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                :loading="analysisStatus.isAnalyzing"
                @click="runEval"
              >
                开始测试
              </el-button>
            </el-form-item>
          </el-form>

          <el-row :gutter="20" style="margin-top: 20px">
            <!-- 左侧：模型参数 -->
            <el-col :span="12">
              <el-card class="equal-height-card">
                <template #header>
                  <div class="card-header font-bold">
                    <span>模型参数</span>
                  </div>
                </template>
                <el-descriptions :column="2" border>
                  <el-descriptions-item
                    v-show="viewRusultFlag"
                    label="模型名称"
                  >
                    {{ selectedModelName }}
                  </el-descriptions-item>
                  <el-descriptions-item v-show="viewRusultFlag" label="测试集">
                    {{ selectedTestDatasetName }}
                  </el-descriptions-item>
                  <el-descriptions-item label="训练集">
                    {{ modelParams.datasetName }}
                  </el-descriptions-item>
                  <el-descriptions-item label="学习率">
                    {{ modelParams.learningRate }}
                  </el-descriptions-item>
                  <el-descriptions-item label="序列长度">
                    {{ modelParams.sequenceLength }}
                  </el-descriptions-item>
                  <el-descriptions-item label="批次数">
                    {{ modelParams.numBatches }}
                  </el-descriptions-item>
                  <el-descriptions-item label="批大小">
                    {{ modelParams.batchSize }}
                  </el-descriptions-item>
                  <el-descriptions-item label="保存/训练轮次">
                    {{ modelParams.seletedEpoch }}/{{ modelParams.epochs }}
                  </el-descriptions-item>
                  <el-descriptions-item label="优化器">
                    {{ modelParams.optimizer }}
                  </el-descriptions-item>
                  <el-descriptions-item label="训练时间">
                    {{ modelParams.trainTime }}
                  </el-descriptions-item>
                </el-descriptions>
              </el-card>
            </el-col>

            <!-- 右侧：样本分布 -->
            <el-col v-show="!viewRusultFlag" :span="12">
              <el-card class="equal-height-card">
                <template #header>
                  <div class="card-header font-bold">
                    <span>测试集样本分布</span>
                  </div>
                </template>
                <div
                  id="distribution-chart"
                  style="width: 100%; height: 250px; margin-top: -60px"
                />
              </el-card>
            </el-col>
            <el-col v-show="viewRusultFlag" :span="12">
              <el-card class="equal-height-card">
                <template #header>
                  <div class="card-header font-bold">
                    <span>样本分布</span>
                  </div>
                </template>
                <div
                  id="twoDistribution-chart"
                  style="
                    width: 500%;
                    height: 300px;
                    margin-left: 100px;
                    margin-top: -20px;
                  "
                />
              </el-card>
            </el-col>
          </el-row>

          <el-row :gutter="20" style="margin-top: 20px">
            <el-col :span="12">
              <el-card class="equal-height-card">
                <template #header>
                  <div class="card-header font-bold">
                    <span>性能指标</span>
                  </div>
                </template>
                <div id="metrics-chart" style="width: 100%; height: 250px" />
              </el-card>
            </el-col>
            <el-col :span="12">
              <el-card class="equal-height-card">
                <template #header>
                  <div class="card-header font-bold">
                    <span>性能指标详情</span>
                  </div>
                </template>
                <el-descriptions :column="1" border>
                  <el-descriptions-item label="准确率">
                    {{ performanceMetrics.accuracy.toFixed(4) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="损失值">
                    {{ performanceMetrics.loss.toFixed(4) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="推理速度">
                    {{ performanceMetrics.inferenceSpeed.toFixed(2) }} ms
                  </el-descriptions-item>
                  <el-descriptions-item label="召回率">
                    {{ performanceMetrics.recall.toFixed(4) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="精确率">
                    {{ performanceMetrics.precision.toFixed(4) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="F1">
                    {{ performanceMetrics.f1.toFixed(4) }}
                  </el-descriptions-item>
                  <el-descriptions-item label="吞吐量">
                    {{ performanceMetrics.throughput.toFixed(2) }} samples/s
                  </el-descriptions-item>
                </el-descriptions>
              </el-card>
            </el-col>
          </el-row>
        </el-card>
      </el-col>
    </el-row>
    <el-card v-show="!viewRusultFlag" class="mt-4">
      <template #header>
        <div class="text-lg font-bold">
          <span>评估记录</span>
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
          <span class="link" :title="`下载模型：${row.modelName}`">{{
            row.modelName
          }}</span>
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
          <el-button type="primary" size="small" @click="viewResult(row)">
            查看结果
          </el-button>
          <el-button type="danger" size="small" @click="deleteRow(row)">
            删除记录
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

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.upload-demo {
  display: flex;
  align-items: center;
}
.form-flex {
  display: flex;
  width: 100%;
  align-items: center;
}
.long-select {
  width: 240px;
}
.equal-height-card {
  height: 100%;
  display: flex;
  flex-direction: column;
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
