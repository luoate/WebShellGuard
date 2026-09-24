// 模拟后端动态生成路由
import { defineFakeRoute } from "vite-plugin-fake-server/client";

/**
 * roles：页面级别权限，这里模拟二种 "admin"、"common"
 * admin：管理员角色
 * common：普通角色
 */
// const systemManagementRouter = {
//   path: "/list",
//   redirect: "/list/card",
//   meta: {
//     showLink: false,
//     icon: "ri:list-check",
//     title: "List"
//   },
//   children: [
//     {
//       path: "/list/card/index",
//       name: "CardList",
//       // component: "list/card/index",
//       meta: {
//         icon: "ri:bank-card-line",
//         title: "List",
//         showParent: true,
//         roles: ["admin"]
//       }
//     }
//   ]
// };

// const permissionRouter = {
//   path: "/permission",
//   meta: {
//     showLink: false,
//     title: "权限管理",
//     icon: "ep:lollipop",
//     rank: 10
//   },
//   children: [
//     {
//       path: "/permission/page/index",
//       name: "PermissionPage",
//       meta: {
//         title: "页面权限",
//         roles: ["admin", "common"]
//       }
//     },
//     {
//       path: "/permission/button",
//       meta: {
//         title: "按钮权限",
//         roles: ["admin", "common"]
//       },
//       children: [
//         {
//           path: "/permission/button/router",
//           component: "permission/button/index",
//           name: "PermissionButtonRouter",
//           meta: {
//             title: "路由返回按钮权限",
//             auths: [
//               "permission:btn:add",
//               "permission:btn:edit",
//               "permission:btn:delete"
//             ]
//           }
//         },
//         {
//           path: "/permission/button/login",
//           component: "permission/button/perms",
//           name: "PermissionButtonLogin",
//           meta: {
//             title: "登录接口返回按钮权限"
//           }
//         }
//       ]
//     }
//   ]
// };

const adminAndtrainerRouter = {
  path: "/",
  redirect: "/model",
  meta: {
    // icon: "ri:list-check",
    icon: "ri:shape-fill",
    title: "模型训练",
    rank: 3
  },
  children: [
    {
      path: "/dataset",
      name: "Dataset",
      component: "dataset/index",
      meta: {
        icon: "dashicons:database",
        title: "数据集操作",
        roles: ["admin", "trainer"]
      }
    },
    {
      path: "/model",
      name: "Model",
      component: "model/index",
      meta: {
        icon: "ep:flag",
        title: "模型训练",
        roles: ["admin", "trainer"]
      }
    },
    {
      path: "/modelEval",
      name: "ModelEval",
      component: "modelEval/index",
      meta: {
        icon: "dashicons:chart-pie",
        title: "模型评估",
        roles: ["admin", "trainer"]
      }
    }
  ]
};

const usersRouter = {
  path: "/users",
  name: "Users",
  component: "users/index",
  meta: {
    // icon: "dashicons:megaphone",
    icon: "dashicons:admin-users",
    title: "用户管理",
    // keepAlive: true,
    rank: 5,
    roles: ["admin"]
  }
};

const listsRouter = {
  path: "/lists",
  name: "Lists",
  component: "lists/index",
  meta: {
    // icon: "dashicons:megaphone",
    icon: "ri:list-check",
    title: "黑白名单管理",
    // keepAlive: true,
    rank: 4,
    roles: ["admin"]
  }
};

export default defineFakeRoute([
  {
    url: "/get-async-routes",
    method: "get",
    response: () => {
      return {
        success: true,
        data: [adminAndtrainerRouter, usersRouter, listsRouter]
      };
    }
  }
]);
