export default [
  {
    path: "/account",
    name: "Account",
    component: () => import("@/views/account/index.vue"),
    meta: {
      // icon: "dashicons:megaphone",
      icon: "dashicons:admin-generic",
      title: "账户设置",
      rank: 6
    }
  }
];
