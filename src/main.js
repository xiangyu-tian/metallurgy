import { createApp } from "vue";
import App from "./App.vue";
import router from "./router";
// import store from "./store";
import "@/assets/css/initialization.css";
import 'animate.css';
// 引入 Font Awesome
import '@fortawesome/fontawesome-free/css/all.css';
// 1. 导入封装的request
import request from './utils/request';
// import WOW from 'wow.js';

const app = createApp(App);

// 2. 全局挂载axios实例（添加这一行）
app.config.globalProperties.$axios = request;

app.use(router);
// app.use(store); // 如果你有 store 的话
app.mount('#app');

// const wow = new WOW();
// wow.init();
//
// createApp(App    ).use(store).use(router).mount("#app");