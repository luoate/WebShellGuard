export default [
  {
    path: "/history",
    name: "History",
    component: () => import("@/views/history/index.vue"),
    meta: {
      icon: "ep:grid",
      title: "检测记录",
      keepAlive: true,
      rank: 2
    }
  }
];
