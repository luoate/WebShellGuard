export default [
  {
    path: "/lists",
    name: "Lists",
    component: () => import("@/views/lists/index.vue"),
    meta: {
      showLink: false,
      icon: "ri:list-check",
      title: "黑白名单管理",
      keepAlive: true,
      rank: 4
    }
  }
];
