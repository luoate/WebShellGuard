export default [
  {
    path: "/upload",
    name: "Upload",
    component: () => import("@/views/upload/index.vue"),
    meta: {
      icon: "mdi:clipboard-text-search-outline",
      title: "代码检测",
      keepAlive: true,
      rank: 1
    }
  }
];
