<template>
  <header class="header">
    <div class="containers">
      <div class="bx-header001">
        <div class="pull-left bx-logo">
          <router-link to="/"><img src="../assets/images/logo-icon.png"/>
            <img src="../assets/images/logo.png"/></router-link>
        </div>

        <div class="pull-right bx-navigation">
          <div class="hamburger bx-sj1" :class="headerOn?'is-active':''" id="hamburger-1" @click="openNav">
            <span class="line"></span><span class="line"></span
          ><span class="line"></span>
          </div>
        </div>

        <div class="pull-right bx-lang">
          <span class="bx-lang-list active">中</span>
          <span class="bx-lang-list">英</span>

          <!-- 登录状态显示用户信息 -->
          <div v-if="isLoggedIn" class="user-info-container">
            <div class="user-display" @click="toggleUserMenu">
              <span class="user-avatar">{{ userAvatar }}</span>
              <span class="user-name">{{ displayName }}</span>
              <span v-if="userRole === 'admin'" class="user-role-tag">（管理员）</span>
              <i class="fas fa-chevron-down user-dropdown-icon"></i>
            </div>

            <!-- 用户下拉菜单 - 使用现有导航下拉菜单样式 -->
            <div v-if="showUserMenu" class="bx-nav-fd user-dropdown-menu">
              <p>
                <router-link to="/profile" class="dropdown-item">
                  <i class="fas fa-user-circle"></i> 个人中心
                </router-link>
              </p>
              <p>
                <a href="#" class="dropdown-item logout-item" @click.prevent="logout">
                  <i class="fas fa-sign-out-alt"></i> 退出登录
                </a>
              </p>
            </div>
          </div>

          <!-- 未登录状态显示登录注册 - 保持原有样式 -->
          <div v-else class="auth-links">
            <router-link to="/login" class="bx-lang-list_1">登录</router-link>
            <span>|</span>
            <router-link to="/register" class="bx-lang-list_2">注册</router-link>
          </div>
        </div>

        <div class="bx-nav pull-right" :class="headerOn?'active':''">
          <ul>
            <li class="active">
              <router-link to="/">首页</router-link>
            </li>
            <li>
              <router-link to="/thermodynamics">数据资源</router-link>
              <div class="bx-nav-fd">
                <p>
                  <router-link to="/thermodynamics">热力学数据库</router-link>
                </p>
                <p>
                  <router-link to="/thermodynamics">动力学数据库</router-link>
                </p>
                <p>
                  <router-link to="/thermodynamics">相图数据库</router-link>
                </p>
                <p>
                  <router-link to="/thermodynamics">反应数据库</router-link>
                </p>
                <p>
                  <router-link to="/thermodynamics">数据源目录</router-link>
                </p>
              </div>
            </li>
            <li>
              <router-link to="/scene">智能场景</router-link>
              <div class="bx-nav-fd">
                <p>
                  <router-link to="/scene">模型工具中心</router-link>
                </p>
              </div>
            </li>
            <li>
              <router-link to="/basic-principles">研究领域</router-link>
              <div class="bx-nav-fd">
                <p>
                  <router-link to="/basic-principles">冶金基础原理</router-link>
                </p>
                <p>
                  <router-link to="/steel-metallurgy">钢铁冶金</router-link>
                </p>
                <p>
                  <router-link to="/non-ferrous">有色冶金</router-link>
                </p>
                <p>
                  <router-link to="/energy-restructuring">冶金能源重构</router-link>
                </p>
                <p>
                  <router-link to="/resource-utilization">冶金资源利用</router-link>
                </p>
              </div>
            </li>
            <li>
              <router-link to="/List">科普</router-link>
              <div class="bx-nav-fd">
                <p>
                  <router-link to="/">过程工艺数据</router-link>
                </p>
                <p>
                  <router-link to="/basic-tools">基础工具软件</router-link>
                </p>
              </div>
            </li>
            <li>
              <router-link to="/Introduction">联系我们</router-link>
            </li>
          </ul>
        </div>
      </div>
    </div>
  </header>
</template>

<script>
import { getCurrentUser, isLoggedIn, getDisplayName, getUserEmail, getUserRole, getRoleLabel, getUserAvatar, logout as authLogout } from '@/utils/auth.js';

export default {
  name: "HeaderPage",
  props: {},
  data() {
    return {
      headerOn: false,
      showUserMenu: false,
      isLoggedIn: false,
      displayName: '',
      userEmail: '',
      userRole: '',
      roleLabel: '',
      userAvatar: ''
    }
  },
  methods: {
    openNav() {
      this.headerOn = !this.headerOn
    },

    toggleUserMenu() {
      this.showUserMenu = !this.showUserMenu;
    },

    closeUserMenu() {
      this.showUserMenu = false;
    },

    logout() {
      authLogout();
      this.isLoggedIn = false;
      this.showUserMenu = false;
    },

// Header.vue - updateUserInfo 方法
updateUserInfo() {
  this.isLoggedIn = isLoggedIn();
  if (this.isLoggedIn) {
    // 直接获取用户数据
    const user = getCurrentUser();
    
    this.displayName = getDisplayName();
    this.userEmail = getUserEmail();
    
    // ========== 修改这里：根据 account_type 或 role 判断管理员 ==========
    if (user) {
      const isAdmin = 
        (user.accountType && user.accountType.toLowerCase() === 'admin') ||
        (user.role && user.role.toLowerCase() === 'admin');
      
      this.userRole = isAdmin ? 'admin' : 'user';
      this.roleLabel = isAdmin ? '管理员' : '用户';
      this.userAvatar = getUserAvatar();
    }
  } else {
    this.userRole = '';
    this.roleLabel = '';
    this.userAvatar = '';
  }
},

    handleClickOutside(event) {
      if (!this.$el.contains(event.target)) {
        this.closeUserMenu();
      }
    }
  },
  mounted() {
    this.updateUserInfo();

    window.addEventListener('storage', () => {
      this.updateUserInfo();
    });

    document.addEventListener('click', this.handleClickOutside);
  },
  beforeUnmount() {
    document.removeEventListener('click', this.handleClickOutside);
  }
};
</script>

<style scoped>
/* 样式部分保持不变，无需修改 */
.header {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 90px;
  z-index: 99;
  background-color: transparent;
  transition: all 0.5s;
  background: linear-gradient(180deg, rgb(0, 0, 0), rgba(63, 62, 62, 0));
  backdrop-filter: blur(10px);
}

.containers {
  padding-left: 5%;
  padding-right: 5%;
}

.header.active {
  background-color: #fff;
}

.bx-header001 {
  height: 90px;
  line-height: 90px;
  position: relative;
}

.bx-header001 .bx-logo {
  max-height: 100px;
}

.bx-header001 .bx-logo a {
  display: block;
}

.bx-header001 .bx-logo img {
  max-height: calc(100vw / 40);
  height: 70px;
}

.bx-header001 .bx-nav ul li {
  position: relative;
  float: left;
  line-height: 90px;
  text-align: center;
  font-size: 18px;
  z-index: 600;
  padding: 0 20px;
}

.bx-header001 .bx-nav ul li a {
  display: block;
  color: #fff;
  font-weight: 400;
  position: relative;
  padding: 0 5px;
}

.bx-header001 .bx-navigation {
  display: none;
  margin-left: 10px;
}

.bx-header001 .bx-nav ul li a:hover,
.bx-header001 .bx-nav ul li.active a {
  font-weight: 700;
}

.bx-navigation {
  display: none;
}

/* 语言切换和用户信息区域 */
.bx-lang {
  display: flex;
  align-items: center;
  height: 90px;
  margin-left: 20px;
  position: relative;
}

.bx-lang-list {
  display: block;
  width: 50px;
  line-height: 38px;
  height: 38px;
  text-align: center;
  background-color: rgba(0, 70, 219, .4);
  color: rgb(255, 254, 254);
  font-size: 18px;
  cursor: pointer;
}

.bx-lang-list.active {
  background-color: #0046DB;
  color: #fff;
}

/* 登录注册链接样式 */
.auth-links {
  display: flex;
  align-items: center;
  margin-left: 20px;
}

.bx-lang-list_1,
.bx-lang-list_2 {
  font-size: 18px;
  margin-left: 8px;
  margin-right: 8px;
  color: rgb(255, 254, 254);
  text-decoration: none;
  cursor: pointer;
  transition: color 0.3s ease;
}

.bx-lang-list_1:hover,
.bx-lang-list_2:hover {
  color: #80d0ff;
}

/* 用户信息容器 */
.user-info-container {
  position: relative;
  display: inline-block;
  margin-left: 10px;
}

/* 用户显示区域 - 模仿导航项样式 */
.user-display {
  display: inline-flex;
  align-items: center;
  cursor: pointer;
  padding: 0 15px;
  position: relative;
  height: 90px;
  line-height: 90px;
}

/* 用户头像 - 添加圆形边框 */
.user-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 32px;
  height: 32px;
  font-weight: 700;
  font-size: 16px;
  margin-right: 10px;
  color: #fff;
  border: 2px solid rgba(255, 255, 255, 0.4); /* 添加圆形边框 */
  border-radius: 50%; /* 确保圆形 */
  background-color: rgba(0, 70, 219, 0.3); /* 轻微背景色 */
}

/* 用户名 - 模仿导航链接样式 */
.user-name {
  color: #fff;
  font-weight: 400;
  font-size: 18px;
}

/* 用户角色标签 */
.user-role-tag {
  color: #80d0ff;
  font-size: 14px;
  margin-left: 4px;
  font-weight: 400;
}

/* 下拉箭头 */
.user-dropdown-icon {
  color: #fff;
  font-size: 12px;
  margin-left: 8px;
  transition: transform 0.3s ease;
}

.user-display:hover .user-dropdown-icon {
  transform: rotate(180deg);
}

/* 用户下拉菜单 - 完全使用现有导航下拉菜单样式 */
.user-info-container .bx-nav-fd.user-dropdown-menu {
  position: absolute;
  top: 90px;
  left: 50%;
  transform: translateX(-50%);
  line-height: 30px;
  min-width: 160px;
  z-index: 600;
  background: linear-gradient(180.00deg, rgb(0, 84, 223), rgb(12, 53, 146) 100%);
  box-shadow: 0 8px 20px 0px rgba(180, 184, 206, 0.14);
  border-radius: 10px;
  padding: 10px 0;
  display: none;
}

.user-info-container:hover .bx-nav-fd.user-dropdown-menu {
  display: block;
}

/* 下拉菜单项样式 - 保持现有样式 */
.user-dropdown-menu .dropdown-item {
  display: flex;
  align-items: center;
  padding: 8px 20px;
  color: #fff;
  text-decoration: none;
  font-weight: 400;
  transition: all 0.3s ease;
}

.user-dropdown-menu .dropdown-item:hover {
  font-weight: bold;
  background-color: rgba(255, 255, 255, 0.1);
}

.user-dropdown-menu .dropdown-item i {
  margin-right: 10px;
  width: 16px;
  text-align: center;
}

/* 退出登录项特殊样式 */
.logout-item {
  color: #ff9999;
}

.logout-item:hover {
  color: #ff6666;
}

/* 悬停效果 - 模仿导航项 */
.user-display:hover .user-name {
  font-weight: 700;
}

/* 头像悬停效果 */
.user-display:hover .user-avatar {
  border-color: rgba(255, 255, 255, 0.8);
  background-color: rgba(0, 70, 219, 0.5);
  transform: scale(1.05);
  transition: all 0.3s ease;
}

/* 导航下拉菜单 */
.bx-header001 .bx-nav ul li .bx-nav-fd {
  position: absolute;
  top: 90px;
  left: 0;
  line-height: 30px;
  min-width: 180px;
  background-color: #ffffff;
  z-index: 600;
  background: linear-gradient(180.00deg, rgb(0, 84, 223), rgb(12, 53, 146) 100%);
  box-shadow: 0 8px 20px 0px rgba(180, 184, 206, 0.14);
  border-radius: 10px;
  padding: 10px 0;
  display: none;
}

.bx-header001 .bx-nav ul li .bx-nav-fd a {
  padding: 5px 5px;
  color: #fff;
  font-weight: 400;
}

.bx-header001 .bx-nav ul li:hover .bx-nav-fd {
  display: block;
}

.bx-header001 .bx-nav ul li .bx-nav-fd a:hover {
  font-weight: bold;
}

/* 响应式设计 */
@media (max-width: 1600px) {
  .bx-header001 .bx-nav ul li {
    padding: 0 15px;
    font-size: 16px;
  }

  .bx-lang-list {
    font-size: 16px;
  }

  .containers {
    padding-left: 3%;
    padding-right: 3%;
  }

  .bx-lang {
    margin-left: 15px;
  }

  .auth-links {
    margin-left: 15px;
  }

  .user-info-container {
    margin-left: 15px;
  }

  .user-name {
    font-size: 16px;
  }

  .user-avatar {
    width: 30px;
    height: 30px;
    font-size: 15px;
    margin-right: 8px;
  }
}

@media (max-width: 1400px) {
  .bx-header001 .bx-nav ul li {
    padding: 0 10px;
    font-size: 15px;
  }

  .bx-lang-list {
    width: 38px;
    line-height: 33px;
    height: 33px;
  }

  .user-name {
    font-size: 15px;
  }

  .user-avatar {
    width: 28px;
    height: 28px;
    font-size: 14px;
    margin-right: 8px;
  }

  .user-role-tag {
    font-size: 13px;
  }
}

@media (max-width: 1200px) {
  .bx-header001 .bx-nav ul li {
    position: relative;
    float: left;
    line-height: 90px;
    text-align: center;
    font-size: 18px;
    z-index: 600;
    padding: 0 20px;
  }

  .bx-lang {
    display: flex;
    align-items: center;
    height: 90px;
    margin-left: 20px;
  }

  .bx-header001 .bx-nav ul li .bx-nav-fd {
    position: absolute;
    top: 90px;
    left: 50%;
    line-height: 30px;
    min-width: 180px;
    background-color: #ffffff;
    z-index: 600;
    background: linear-gradient(180.00deg, rgb(0, 84, 223), rgb(12, 53, 146) 100%);
    box-shadow: 0 8px 20px 0px rgba(180, 184, 206, 0.14);
    border-radius: 10px;
    padding: 10px 0;
    display: none;
  }

  .bx-header001 {
    height: 60px;
    line-height: 60px;
  }

  .bx-header001 .bx-logo img {
    max-height: calc(100vw / 20);
  }

  .bx-header001 .bx-nav {
    display: none;
    position: fixed;
    top: 60px;
    z-index: 500;
    left: 0;
    z-index: 600;
    width: 100%;
    background-color: #fff;
    max-height: calc(100vh - 165px);
    overflow-y: auto;
  }

  .bx-header001 .bx-nav ul li {
    line-height: 1;
    text-align: left;
    float: none;
    border-bottom: 1px solid #eee;
    padding: 15px 10px;
  }

  .bx-header001 .bx-nav ul li i {
    display: block;
    width: 12px;
    height: 12px;
    color: #333;
    transition: color 0.25s;
    position: absolute;
    right: 10px;
    top: 18px;
  }

  .bx-header001 .bx-nav ul li i::before {
    content: "";
    position: absolute;
    left: 0;
    top: 50%;
    width: 100%;
    height: 2px;
    background-color: #333;
    transform: translate(0, -50%);
  }

  .bx-header001 .bx-nav ul li i::after {
    content: "";
    position: absolute;
    left: 50%;
    top: 0;
    width: 2px;
    height: 100%;
    background-color: #333;
    transform: translate(-50%, 0);
  }

  .bx-header001 .bx-nav ul li a {
    padding: 0;
    color: #333;
    text-align: left;
    font-size: 16px;
  }

  .bx-header001 .bx-navigation {
    display: block;
  }

  .bx-header001 .bx-nav ul li .bx-nav-fd {
    display: none;
    position: relative;
    top: 0px;
    width: 100%;
    padding: 0;
    padding-left: 20px;
    box-shadow: none;
    display: block;
    background: transparent;
    margin-top: 15px;
  }

  .bx-header001 .bx-nav ul li .bx-nav-fd p {
    display: inline-block;
    width: 48%;
  }

  .bx-navigation {
    display: block;
  }

  .bx-header001 .bx-nav ul li .bx-nav-fd a {
    padding: 0 5px;
    font-size: 15px;
    color: #000;
  }

  .hamburger {
    margin-top: 18px;
  }

  .hamburger .line {
    width: 35px;
    height: 3px;
    background-color: #fff;
    display: block;
    margin: 8px auto;
    -webkit-transition: all 0.3s ease-in-out;
    -o-transition: all 0.3s ease-in-out;
    transition: all 0.3s ease-in-out;
  }

  .hamburger:hover {
    cursor: pointer;
  }

  .active .hamburger .line {
    background-color: #000;
  }

  #hamburger-1.is-active .line:nth-child(2) {
    opacity: 0;
  }

  #hamburger-1.is-active .line:nth-child(1) {
    -webkit-transform: translateY(13px) rotate(45deg);
    -ms-transform: translateY(13px) rotate(45deg);
    -o-transform: translateY(13px) rotate(45deg);
    transform: translateY(11px) rotate(45deg);
  }

  #hamburger-1.is-active .line:nth-child(3) {
    -webkit-transform: translateY(-13px) rotate(-45deg);
    -ms-transform: translateY(-13px) rotate(-45deg);
    -o-transform: translateY(-13px) rotate(-45deg);
    transform: translateY(-11px) rotate(-45deg);
  }

  .bx-header001 .bx-nav ul li a:hover,
  .bx-header001 .bx-nav ul li a.active {
    color: #0046DB !important;
  }

  .bx-header001 .bx-nav ul li a::after {
    display: none;
  }

  /* 移动端用户信息适配 */
  .bx-lang {
    height: 90px;
    margin-left: 0;
    margin-right: 10px;
  }

  .auth-links {
    margin-left: 0;
  }

  .bx-lang-list_1,
  .bx-lang-list_2 {
    font-size: 18px;
    margin-left: 8px;
    margin-right: 8px;
    color: rgb(255, 254, 254);
    text-decoration: none;
    cursor: pointer;
  }

  .bx-lang-list_1:hover,
  .bx-lang-list_2:hover {
    color: #0046db;
  }

  /* 移动端用户信息显示 */
  .user-info-container {
    margin-left: 10px;
  }

  .user-display {
    height: 60px;
    line-height: 60px;
    padding: 0 10px;
  }

  .user-avatar {
    width: 26px;
    height: 26px;
    font-size: 13px;
    margin-right: 6px;
    border-width: 1.5px;
  }

  .user-name {
    font-size: 16px;
  }

  .user-role-tag {
    font-size: 12px;
  }

  /* 移动端下拉菜单 */
  .user-info-container .bx-nav-fd.user-dropdown-menu {
    top: 60px;
    position: fixed;
    left: 20px;
    right: 20px;
    transform: none;
    min-width: auto;
    width: calc(100% - 40px);
    max-width: 300px;
    margin: 0 auto;
  }

  .user-info-container:hover .bx-nav-fd.user-dropdown-menu {
    display: block;
  }

  .user-dropdown-menu .dropdown-item {
    padding: 10px 20px;
    font-size: 15px;
  }
}
</style>