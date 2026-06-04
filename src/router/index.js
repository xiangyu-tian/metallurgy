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
    },
    {
      path: '/basic-principles',
      name: 'BasicPrinciples',
      component: () => import('../views/BasicPrinciples.vue'),
      meta: { title: "冶金基础原理 - 冶金平台" }
    },
    {
      path: '/steel-metallurgy',
      name: 'SteelMetallurgy',
      component: () => import('../views/SteelMetallurgy.vue'),
      meta: { title: "钢铁冶金 - 冶金平台" }
    },
    {
      path: '/non-ferrous',
      name: 'NonFerrous',
      component: () => import('../views/NonFerrous.vue'),
      meta: { title: "有色冶金 - 冶金平台" }
    },
    {
      path: '/energy-restructuring',
      name: 'EnergyRestructuring',
      component: () => import('../views/EnergyRestructuring.vue'),
      meta: { title: "冶金能源重构 - 冶金平台" }
    },
    {
      path: '/resource-utilization',
      name: 'ResourceUtilization',
      component: () => import('../views/ResourceUtilization.vue'),
      meta: { title: "冶金资源利用 - 冶金平台" }
    },
    {
      path: '/scene/thermodynamics',
      name: 'SceneThermodynamics',
      component: () => import('../views/SceneThermodynamics.vue'),
      meta: { title: "热力学推理 - 冶金平台" }
    },
    {
      path: '/scene/converter',
      name: 'SceneConverter',
      component: () => import('../views/SceneConverter.vue'),
      meta: { title: "转炉炼钢工艺优化 - 冶金平台" }
    },
    {
      path: '/scene/blastfurnace',
      name: 'SceneBlastfurnace',
      component: () => import('../views/SceneBlastfurnace.vue'),
      meta: { title: "高炉低碳运行分析 - 冶金平台" }
    },
    {
      path: '/scene/casting',
      name: 'SceneCasting',
      component: () => import('../views/SceneCasting.vue'),
      meta: { title: "连铸质量辅助决策 - 冶金平台" }
    },
    {
      path: '/scene',
      name: 'Scene',
      component: () => import('../views/SceneLayout.vue'),
      meta: { title: "智能场景 - 冶金平台" }
    },
    {
      path: '/scene/simulation',
      name: 'SceneSimulation',
      component: () => import('../views/SceneSimulation.vue'),
      meta: { title: "仿真与工单协同 - 冶金平台" }
    },
    {
      path: '/scene/thermodynamics/tool/:toolId',
      name: 'SceneThermoTool',
      component: () => import('../views/SceneThermoTool.vue'),
      meta: { title: "热力学推理 - 冶金平台" }
    },
    {
      path: '/scene/converter/tool/:toolId',
      name: 'SceneConverterTool',
      component: () => import('../views/SceneConverterTool.vue'),
      meta: { title: "转炉炼钢工艺优化 - 冶金平台" }
    },
    {
      path: '/scene/blastfurnace/tool/:toolId',
      name: 'SceneBlastTool',
      component: () => import('../views/SceneBlastTool.vue'),
      meta: { title: "高炉低碳运行分析 - 冶金平台" }
    },
    {
      path: '/scene/casting/tool/:toolId',
      name: 'SceneCastingTool',
      component: () => import('../views/SceneCastingTool.vue'),
      meta: { title: "连铸质量辅助决策 - 冶金平台" }
    },
    {
      path: '/scene/simulation/tool/:toolId',
      name: 'SceneSimTool',
      component: () => import('../views/SceneSimTool.vue'),
      meta: { title: "仿真与工单协同 - 冶金平台" }
    }
  ]
});

// 跳转后自动返回页面顶部
router.afterEach(() => {
  window.scrollTo(0,0);
});

export default router;