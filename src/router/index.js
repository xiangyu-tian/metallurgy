import { createRouter, createWebHistory } from "vue-router";
import Index from "../views/Index.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: "/",
      name: "home",
      component: Index,
    },
    {
      path: "/Prediction",
      name: "Prediction",
      component: () =>
          import("../views/Prediction.vue"),
    },
    {
      path: "/List",
      name: "List",
      component: () =>
          import("../views/List.vue"),
    },
    {
      path: "/Introduction",
      name: "Introduction",
      component: () =>
          import("../views/Introduction.vue"),
    },
    {
      path: "/Search",
      name: "Search",
      component: () =>
          import("../views/Search.vue"),
    },
    {
      path: "/login",
      name: "UserLogin",
      component: () =>
          import("../views/Login.vue"),
    },
    {
      path: "/register",
      name: "UserRegister",
      component: () =>
          import("../views/Register.vue"),
    },
    {
      path: "/thermodynamics",
      name: "Thermodynamics",
      component: () => import("../views/Thermodynamics.vue"),
    },
    {
      path: "/carbon-emission",
      name: "CarbonEmission",
      component: () => import("../views/CarbonEmission.vue"),
    },
    {
      "path": "/fluid-dynamics",
      "name": "FluidDynamics",
      "component": () => import("../views/FluidDynamics.vue"),
    },
    {
      path: "/electrochemical",
      name: "Electrochemical",
      component: () => import("../views/Electrochemical.vue"),
    },
    {
      path: "/process-data",
      name: "ProcessData",
      component: () => import("../views/ProcessData.vue"),
      meta: {
        title: "工艺数据 - 工业数据库系统"
      }
    },
    {
      path: "/basic-tools",
      name: "BasicTools",
      component: () => import("../views/BasicTools.vue"),
      meta: {
        title: "基础工具软件 - 工业数据库系统"
      }
    },
    {
      path: '/profile',
      name: 'Profile',
      component: () => import('../views/Profile.vue'),
      meta: {
        requiresAuth: true // 需要登录
      }
    },
    {
      path: '/chat',
      name: 'Chat',
      component: () => import('../views/Chat.vue'),
      meta: {
        title: "智能对话 - 冶金平台"
      }
    }
    // =================================
  ]
});

// 跳转后自动返回页面顶部
router.afterEach(() => {
  window.scrollTo(0,0);
});

export default router;