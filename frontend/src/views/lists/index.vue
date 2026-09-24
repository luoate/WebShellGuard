<script setup lang="ts">
import { ref, reactive, onMounted } from "vue";
import axios from "axios";
import { message } from "@/utils/message";
import { useUserStoreHook } from "@/store/modules/user";

defineOptions({
  name: "Lists"
});

const listType = ref("black"); // black or white
const dialogForm = reactive({
  id: null,
  fileName: "",
  hash: "",
  fileSize: "",
  type: "black",
  file: null
});

const searchForm = reactive({
  target: ""
});

const rules = {
  // file: [{ required: true, message: "请上传文件", trigger: "change" }],
  fileName: [{ required: true, message: "请输入文件名", trigger: "blur" }],
  hash: [{ required: true, message: "请输入哈希值", trigger: "blur" }],
  fileSize: [{ required: true, message: "请输入文件大小", trigger: "blur" }]
};

const formRef = ref();
const dataList = ref([]);
const loading = ref(false);
const dialogVisible = ref(false);
const dialogTitle = ref("新增条目");
const dialogType = ref("add");
const currentRow = ref(null);
const error = ref(null);

const pagination = reactive({
  total: 0,
  pageSize: 10,
  currentPage: 1
});

const onSearch = async () => {
  try {
    loading.value = true;
    error.value = null;
    // const username = useUserStoreHook().username;
    // console.log(123);
    const response = await axios.get("http://127.0.0.1:11451/list/info", {
      params: {
        type: listType.value,
        search: searchForm.target,
        page: pagination.currentPage,
        pageSize: pagination.pageSize
      }
    });
    tableData.value = (response.data.list || []).map(item => ({
      id: item.id, // 数据库中的id
      fileName: item.fileName, // 文件名
      hash: item.hash, // 文件的SHA-256值
      fileSize: item.fileSize, // 文件大小
      type: item.type, // 类型（black或white）
      user: item.user, // 用户名
      createTime: item.createTime // 创建时间
    }));
    console.log(response.data.list);
    console.log(tableData.value);
    pagination.total = response.data.total;
  } catch (err) {
    error.value = err.message || "获取用户信息失败";
  } finally {
    loading.value = false;
  }
};

// const resetForm = () => {
//   form.username = "";
//   onSearch();
// };

const handleSizeChange = val => {
  pagination.pageSize = val;
  onSearch();
};

const handleCurrentChange = val => {
  pagination.currentPage = val;
  onSearch();
};

const openDialog = (type = "add", row = null) => {
  dialogType.value = type;
  // console.log(dialogType.value);
  dialogTitle.value = type === "add" ? "新增条目" : "编辑条目";
  currentRow.value = row;

  if (type === "edit") {
    Object.assign(dialogForm, row);
  }

  dialogVisible.value = true;
};

const handleFileChange = file => {
  dialogForm.file = file.raw;
};

const handleDelete = async row => {
  try {
    await axios.post(`http://127.0.0.1:11451/list/delete`, {
      id: row.id
    });

    message(`删除条目成功`, { type: "success" });
    onSearch(); // 重新获取列表
  } catch (err) {
    if (err !== "cancel") {
      // ElMessage.error(
      //   "删除失败：" + (err.response?.data?.error || err.message)
      // );
      message("删除失败：" + (err.response?.data?.error || err.message), {
        type: "error"
      });
    }
  }
};

const resetForm = () => {
  Object.assign(dialogForm, {
    id: null,
    type: "black",
    file: null
  });
  searchForm.target = "";
  onSearch();
};
const username = useUserStoreHook().username;
const submitForm = async () => {
  formRef.value.validate(async valid => {
    // console.log(123);
    // if (!valid) return;
    // console.log(1234);
    try {
      const formData = new FormData();
      formData.append("type", dialogForm.type);
      formData.append("file", dialogForm.file);
      // console.log(dialogForm.file);
      formData.append("user", username);
      // formData.append("description", dialogForm.description);
      // formData.append("status", String(dialogForm.status));

      if (dialogType.value === "add") {
        await axios.post("http://127.0.0.1:11451/list/add", formData, {
          headers: {
            "Content-Type": "multipart/form-data"
          }
        });
        resetForm();
        message("新增条目成功", { type: "success" });
      } else {
        formData.append("id", dialogForm.id);
        formData.append("fileName", dialogForm.fileName);
        formData.append("hash", dialogForm.hash);
        formData.append("fileSize", dialogForm.fileSize);
        formData.append("type", dialogForm.type);
        await axios.post(
          `http://127.0.0.1:11451/list/update?id=${dialogForm.id}`,
          formData,
          {
            headers: {
              "Content-Type": "multipart/form-data"
            }
          }
        );
        resetForm();
        message("编辑条目成功", { type: "success" });
      }

      dialogVisible.value = false;
      onSearch();
    } catch (err) {
      message("提交失败：" + (err.response?.data?.error || err.message), {
        type: "error"
      });
    }
  });
};

onMounted(() => {
  onSearch();
});
// const tableData = ref([]);
const tableData = ref([
  {
    id: "1",
    fileName: "231",
    hash: "sjakhkjashfkjash",
    fileSize: "123",
    type: "black",
    user: "admin",
    createTime: "xxx"
  }
]);
const columns = [
  { label: "ID", prop: "id", align: "center", slot: "id", sortable: true },
  {
    label: "文件名",
    prop: "fileName",
    align: "center",
    slot: "fileName",
    sortable: true
  },
  {
    label: "哈希值",
    prop: "hash",
    align: "center",
    slot: "hash",
    sortable: true
  },
  {
    label: "文件大小(Byte)",
    prop: "fileSize",
    align: "center",
    slot: "fileSize",
    sortable: true
  },
  {
    label: "类型",
    prop: "type",
    align: "center",
    slot: "type",
    sortable: true
  },
  {
    label: "创建人",
    prop: "user",
    align: "center",
    slot: "user",
    sortable: true
  },
  {
    label: "创建时间",
    prop: "createTime",
    align: "center",
    slot: "createTime",
    sortable: true
  },
  {
    label: "操作",
    slot: "operation",
    width: "180",
    align: "center"
  }
];
</script>

<template>
  <div class="app-container">
    <el-card>
      <template #header>
        <div class="text-lg font-bold">
          <span>黑白名单管理</span>
        </div>
      </template>
      <el-form
        ref="formRef"
        :inline="true"
        :model="searchForm"
        class="search-form"
      >
        <el-form-item label="模糊搜索：" prop="target">
          <el-input
            v-model="searchForm.target"
            placeholder="请输入搜索内容"
            clearable
            class="!w-[180px]"
          />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="loading" @click="onSearch">
            搜索
          </el-button>
          <el-button @click="resetForm"> 重置 </el-button>
        </el-form-item>
      </el-form>
      <!-- <el-divider /> -->

      <el-card class="table-container" shadow="never">
        <el-button
          type="primary"
          style="margin-bottom: 15px; margin-top: -20px"
          @click="openDialog()"
        >
          新增条目
        </el-button>

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
          <template #type="{ row }">
            <el-tag :type="row.type === 'white' ? 'success' : 'danger'">
              {{ row.type === "black" ? "黑名单" : "白名单" }}
            </el-tag>
          </template>
          <template #operation="{ row }">
            <el-button
              type="primary"
              size="small"
              @click="openDialog('edit', row)"
            >
              编辑
            </el-button>
            <el-popconfirm title="确认删除该条目?" @confirm="handleDelete(row)">
              <template #reference>
                <el-button type="danger" size="small"> 删除 </el-button>
              </template>
            </el-popconfirm>
          </template>
        </pure-table>
      </el-card>
      <div class="pagination-container">
        <el-pagination
          v-model:current-page="pagination.currentPage"
          v-model:page-size="pagination.pageSize"
          :page-sizes="[5, 10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="handleCurrentChange"
          @size-change="handleSizeChange"
        />
      </div>

      <!-- 新增/编辑对话框 -->
      <el-dialog
        v-model="dialogVisible"
        :title="dialogType === 'add' ? '新增条目' : '编辑条目'"
      >
        <el-form
          ref="formRef"
          :model="dialogForm"
          :rules="rules"
          label-width="80px"
        >
          <el-form-item v-show="dialogType === 'add'" label="文件" prop="file">
            <el-upload
              v-model:file="dialogForm.file"
              class="upload-demo"
              action=""
              :auto-upload="false"
              :limit="1"
              :on-change="handleFileChange"
            >
              <el-button type="primary">选择文件</el-button>
            </el-upload>
          </el-form-item>
          <el-form-item
            v-show="dialogType === 'edit'"
            label="文件名"
            prop="fileName"
          >
            <el-input v-model="dialogForm.fileName" />
          </el-form-item>
          <el-form-item
            v-show="dialogType === 'edit'"
            label="哈希值"
            prop="hash"
          >
            <el-input v-model="dialogForm.hash" />
          </el-form-item>

          <el-form-item
            v-show="dialogType === 'edit'"
            label="文件大小"
            prop="fileSize"
          >
            <el-input v-model="dialogForm.fileSize" />
          </el-form-item>
          <el-form-item label="类型" prop="type">
            <el-select v-model="dialogForm.type" placeholder="请选择类型">
              <el-option label="黑名单" value="black" />
              <el-option label="白名单" value="white" />
            </el-select>
          </el-form-item>
        </el-form>

        <template #footer>
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitForm">提交</el-button>
        </template>
      </el-dialog>
    </el-card>
  </div>
</template>

<style scoped>
.app-container {
  padding: 20px;
}
.search-form {
  margin-bottom: 20px;
}
.table-container {
  background: #fff;
  padding: 20px;
}
.pagination-container {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
  @media (max-width: 768px) {
    justify-content: center;
  }
}
</style>
