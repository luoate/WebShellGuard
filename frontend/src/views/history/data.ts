// tableData.ts
import { ref } from "vue";
// import dayjs from "dayjs";
// const filterTag = (value, row) => {
//   return row.tag === value;
// };

// 定义列信息
export const columns = [
  { label: "文件名", prop: "filename", slot: "filename", sortable: true },
  { label: "Hash", prop: "hash", sortable: true },
  {
    label: "检测结果",
    prop: "tag",
    sortable: true,
    // filters: [
    //   { text: "webshell", value: "true" },
    //   { text: "safe", value: "false" }
    // ],
    // filterMethod: addRow,
    filterPlacement: "bottom-end",
    slot: "tag"
  },
  { label: "上传时间", prop: "time", sortable: true },
  {
    label: "操作",
    width: "180",
    fixed: "right",
    slot: "operation",
    align: "center"
  }
];

interface TableRow {
  filename: string;
  hash: string;
  tag: string;
  time: string;
  content: any;
}

// 响应式的 tableData
export const tableData = ref<TableRow[]>([]);

// 添加新数据的方法
export function addRow(newRow: {
  filename: string;
  hash: string;
  tag: string;
  time: string;
  content: any;
}) {
  tableData.value.push(newRow);
}

// 删除数据的方法
export function removeRow(index: number) {
  tableData.value.splice(index, 1);
}
