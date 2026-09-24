<script setup lang="ts">
import { ref, reactive, onMounted } from "vue";
import axios from "axios";
import { message } from "@/utils/message";

const dialogForm = reactive({
  id: null,
  username: "",
  password: "",
  role: "",
  status: 1,
  phone: ""
});

const searchForm = reactive({
  username: ""
});

const roleMap = {
  1: "管理员",
  2: "训练员",
  3: "普通用户"
};

const rules = {
  username: [{ required: true, message: "请输入用户名", trigger: "blur" }],
  password: [{ required: true, message: "请输入密码", trigger: "blur" }],
  phone: [{ required: true, message: "请输入手机号", trigger: "blur" }]
};

const formRef = ref();
const dataList = ref([]);
const loading = ref(false);
const dialogVisible = ref(false);
const dialogTitle = ref("新增用户");
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
    const response = await axios.get("http://127.0.0.1:11451/user/info", {
      params: {
        search: searchForm.username,
        page: pagination.currentPage,
        pageSize: pagination.pageSize
      }
    });
    // console.log(12223);
    // console.log(response);
    tableData.value = (response.data.list || []).map(item => ({
      id: item[0],
      username: item[1],
      role: item[2],
      status: item[3],
      phone: item[4],
      createTime: item[5]
    }));
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
  dialogTitle.value = type === "add" ? "新增用户" : "编辑用户";
  currentRow.value = row;

  if (type === "edit") {
    Object.assign(dialogForm, row);
  }

  dialogVisible.value = true;
};

const handleDelete = async row => {
  try {
    // await ElMessageBox.confirm(
    //   `确定要删除用户「${row.username}」吗？`,
    //   "提示",
    //   {
    //     confirmButtonText: "确定",
    //     cancelButtonText: "取消",
    //     type: "warning"
    //   }
    // );

    // 发起删除请求
    await axios.post(`http://127.0.0.1:11451/user/delete`, {
      id: row.id
    });

    // ElMessage.success(`删除用户 ${row.username} 成功`);
    message(`删除用户 ${row.username} 成功`, { type: "success" });
    onSearch(); // 重新获取用户列表
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
    username: "",
    password: "",
    role: "",
    status: 1,
    phone: ""
  });
  onSearch();
};

const submitForm = async () => {
  formRef.value.validate(async valid => {
    if (!valid) return;
    try {
      // console.log(form.role);
      if (dialogType.value === "add") {
        await axios.post("http://127.0.0.1:11451/user/add", {
          username: dialogForm.username,
          password: dialogForm.password,
          role: dialogForm.role,
          status: dialogForm.status,
          phone: dialogForm.phone
        });
        resetForm();
        // ElMessage.success("新增用户成功");
        message("新增用户成功", { type: "success" });
      } else {
        await axios.post(
          `http://127.0.0.1:11451/user/update?id=${dialogForm.id}`,
          {
            username: dialogForm.username,
            role: dialogForm.role,
            status: dialogForm.status,
            phone: dialogForm.phone
          }
        );
        resetForm();
        // ElMessage.success("编辑用户成功");
        message("编辑用户成功", { type: "success" });
      }

      dialogVisible.value = false;
      onSearch();
    } catch (err) {
      // ElMessage.error(
      //   "提交失败：" + (err.response?.data?.error || err.message)
      // );
      message("提交失败：" + (err.response?.data?.error || err.message), {
        type: "error"
      });
    }
  });
};

onMounted(() => {
  onSearch();
});
const tableData = ref([
  {
    id: "1",
    username: "admin",
    role: "管理员",
    status: 1,
    phone: "122233",
    createTime: "2025-04-14 20:10:00"
  }
]);
const columns = [
  { label: "用户ID", prop: "id", align: "center", slot: "id" },
  {
    label: "用户名",
    prop: "username",
    align: "center",
    slot: "username"
  },
  { label: "身份", prop: "role", align: "center", slot: "role" },
  { label: "状态", prop: "status", align: "center", slot: "status" },
  { label: "手机号", prop: "phone", align: "center", slot: "phone" },
  {
    label: "创建时间",
    prop: "createTime",
    align: "center",
    slote: "createTime"
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
    <el-form
      ref="formRef"
      :inline="true"
      :model="searchForm"
      class="search-form"
    >
      <el-form-item label="用户名称：" prop="username">
        <el-input
          v-model="searchForm.username"
          placeholder="请输入用户名称"
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

    <div class="table-container">
      <el-button
        type="primary"
        style="margin-bottom: 15px"
        @click="openDialog()"
      >
        新增用户
      </el-button>

      <pure-table
        ref="tableRef"
        v-loading="loading"
        row-key="time"
        :data="tableData"
        :columns="columns"
      >
        <template #status="{ row }">
          <el-tag :type="row.status === 1 ? 'success' : 'danger'">
            {{ row.status === 1 ? "启用" : "禁用" }}
          </el-tag>
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
        <template #role="{ row }">
          {{ roleMap[row.role] || "未知角色" }}
        </template>
        <template #operation="{ row }">
          <el-button
            type="primary"
            size="small"
            @click="openDialog('edit', row)"
          >
            编辑
          </el-button>
          <el-popconfirm title="确认删除该用户?" @confirm="handleDelete(row)">
            <template #reference>
              <el-button type="danger" size="small"> 删除 </el-button>
            </template>
          </el-popconfirm>
        </template>
      </pure-table>

      <el-pagination
        v-model:current-page="pagination.currentPage"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
      />
    </div>

    <!-- 新增/编辑对话框 -->
    <el-dialog
      v-model="dialogVisible"
      :title="dialogType === 'add' ? '新增用户' : '编辑用户'"
    >
      <el-form
        ref="formRef"
        :model="dialogForm"
        :rules="rules"
        label-width="80px"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="dialogForm.username" />
        </el-form-item>

        <el-form-item v-if="dialogType === 'add'" label="密码" prop="password">
          <el-input v-model="dialogForm.password" show-password />
        </el-form-item>

        <el-form-item label="角色" prop="role">
          <el-select v-model="dialogForm.role" placeholder="请选择角色">
            <el-option label="普通用户" :value="3" />
            <el-option label="训练员" :value="2" />
            <el-option label="管理员" :value="1" />
          </el-select>
        </el-form-item>

        <el-form-item label="状态" prop="status">
          <el-switch
            v-model="dialogForm.status"
            :active-value="1"
            :inactive-value="0"
          />
        </el-form-item>

        <el-form-item label="手机号" prop="phone">
          <el-input v-model="dialogForm.phone" />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" @click="submitForm">提交</el-button>
      </template>
    </el-dialog>
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
</style>
