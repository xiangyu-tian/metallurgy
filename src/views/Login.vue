<template>
  <Header></Header>
  <div class="Login">
    <div class="bgcolor">
      <div class="mb-nav">
        <div class="container">
          <p>
            当前位置： <router-link to="/">首页</router-link> >
            <span>用户登录</span>
          </p>
        </div>
      </div>
      <div class="container">
        <div class="login-title wow animate__animated animate__fadeInUp">
          <h2>用户登录</h2>
          <p>欢迎访问绿色低碳钢铁冶金全国重点实验室平台</p>
        </div>

        <div class="login-container wow animate__animated animate__fadeInUp">
          <div class="login-left">
            <div class="welcome-section">
              <h3><i class="fas fa-rocket"></i> 平台优势</h3>
              <p class="welcome-text">
                登录后即可访问平台所有功能，包括海量冶金数据库、专业计算工具和AI智能分析系统，助您高效开展研究工作。
              </p>

              <div class="stats-grid">
                <div class="stat-item">
                  <div class="stat-number">540,000+</div>
                  <div class="stat-label">材料数据</div>
                </div>
                <div class="stat-item">
                  <div class="stat-number">50+</div>
                  <div class="stat-label">计算工具</div>
                </div>
                <div class="stat-item">
                  <div class="stat-number">24/7</div>
                  <div class="stat-label">稳定服务</div>
                </div>
                <div class="stat-item">
                  <div class="stat-number">AI</div>
                  <div class="stat-label">智能预测</div>
                </div>
              </div>
            </div>

            <div class="platform-features">
              <h4><i class="fas fa-star"></i> 平台核心功能</h4>
              <div class="features-list">
                <div class="feature-item">
                  <i class="fas fa-check-circle"></i>
                  <span>冶金流体力学计算</span>
                </div>
                <div class="feature-item">
                  <i class="fas fa-check-circle"></i>
                  <span>热力学模拟分析</span>
                </div>
                <div class="feature-item">
                  <i class="fas fa-check-circle"></i>
                  <span>材料性能AI预测</span>
                </div>
                <div class="feature-item">
                  <i class="fas fa-check-circle"></i>
                  <span>碳排放核算工具</span>
                </div>
                <div class="feature-item">
                  <i class="fas fa-check-circle"></i>
                  <span>光谱仪数据集成</span>
                </div>
                <div class="feature-item">
                  <i class="fas fa-check-circle"></i>
                  <span>CFD网格生成</span>
                </div>
              </div>
            </div>
          </div>

          <div class="login-right">
            <div class="login-card">
              <div class="login-card-header">
                <h3><i class="fas fa-sign-in-alt"></i> 登录平台</h3>
                <p>请输入您的账号信息</p>
              </div>

              <!-- 错误提示 -->
              <div v-if="errorMessage" class="error-message">
                <i class="fas fa-exclamation-circle"></i> {{ errorMessage }}
              </div>

              <form class="login-form" @submit.prevent="handleLogin">
                <div class="form-group">
                  <div class="input-with-icon">
                    <i class="fas fa-envelope"></i>
                    <input
                        type="email"
                        v-model="loginForm.email"
                        placeholder="邮箱地址"
                        required
                        :disabled="loading"
                        @keyup.enter="handleLogin"
                        autocomplete="email"
                    />
                  </div>
                </div>

                <div class="form-group">
                  <div class="input-with-icon">
                    <i class="fas fa-lock"></i>
                    <input
                        type="password"
                        v-model="loginForm.password"
                        placeholder="密码"
                        required
                        :disabled="loading"
                        @keyup.enter="handleLogin"
                        autocomplete="current-password"
                    />
                  </div>
                </div>

                <div class="form-options">
                  <div class="remember-me">
                    <input
                        type="checkbox"
                        id="remember"
                        v-model="loginForm.remember"
                        :disabled="loading"
                    />
                    <label for="remember">记住我</label>
                  </div>
                  <a href="#" class="forgot-password" @click.prevent="showForgotPassword">
                    忘记密码？
                  </a>
                </div>

                <button
                    type="submit"
                    class="login-button"
                    :disabled="loading || !loginForm.email || !loginForm.password"
                >
                  <i class="fas fa-sign-in-alt"></i>
                  {{ loading ? '登录中...' : '登录' }}
                  <span v-if="loading" class="loading-spinner"></span>
                </button>

                <div class="divider">
                  <span>或</span>
                </div>

                <div class="social-login">
                  <button
                      type="button"
                      class="social-button wechat"
                      :disabled="loading"
                      @click="showComingSoon"
                  >
                    <i class="fab fa-weixin"></i> 微信登录
                  </button>
                  <button
                      type="button"
                      class="social-button qq"
                      :disabled="loading"
                      @click="showComingSoon"
                  >
                    <i class="fab fa-qq"></i> QQ登录
                  </button>
                </div>

                <div class="register-prompt">
                  <span class="prompt-text">还没有账号？</span>
                  <router-link to="/register" class="register-link">立即注册</router-link>
                </div>
              </form>
            </div>
          </div>
        </div>
      </div>
    </div>
    <Footer></Footer>
  </div>
</template>

<script>
import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";

export default {
  name: "UserLogin",
  components: {
    Header,
    Footer,
  },
  data() {
    return {
      loginForm: {
        email: "",
        password: "",
        remember: false,
      },
      loading: false,
      errorMessage: "",
    };
  },
  methods: {
    async handleLogin() {
      // 重置错误信息
      this.errorMessage = "";

      // 表单验证
      if (!this.loginForm.email.trim()) {
        this.errorMessage = "请输入邮箱地址";
        return;
      }

      if (!this.loginForm.password) {
        this.errorMessage = "请输入密码";
        return;
      }

      // 邮箱格式验证
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(this.loginForm.email)) {
        this.errorMessage = "请输入有效的邮箱地址";
        return;
      }

      this.loading = true;

      try {
        // 使用 this.$axios 发送请求
        const response = await this.$axios.post('/auth/login', {
          email: this.loginForm.email,
          password: this.loginForm.password
        });

// Login.vue - 只修改管理员判断逻辑，其他保持原样
if (response.code === 200) {
  // 检查是否为管理员账户
  const userData = response.data;
  let isAdmin = false;

  // ========== 修改这里：根据 account_type 或 role 判断管理员 ==========
  if (userData.accountType && userData.accountType.toLowerCase() === 'admin') {
    isAdmin = true;
  }
  if (userData.role && userData.role.toLowerCase() === 'admin') {
    isAdmin = true;
  }
  
  // 添加管理员标识到用户数据
  userData.isAdmin = isAdmin;

  // 存储用户信息到 localStorage
  localStorage.setItem('user', JSON.stringify(userData));

  // 存储登录状态
  localStorage.setItem('isLoggedIn', 'true');

  // 如果是管理员，单独存储标识
  if (isAdmin) {
    localStorage.setItem('isAdmin', 'true');
  } else {
    localStorage.removeItem('isAdmin');
  }

  // 显示成功消息
  this.showSuccessMessage(isAdmin ? '管理员登录成功！' : '登录成功！');

  // ========== 保持原来的跳转逻辑 ==========
  setTimeout(() => {
    this.$router.push('/').then(() => {
      // 触发Header组件更新
      window.dispatchEvent(new Event('storage'));
    });
  }, 800);
  } else {
          // 处理各种错误情况
          if (response.code === 401) {
            this.errorMessage = "邮箱或密码错误";
          } else if (response.code === 404) {
            this.errorMessage = "用户不存在";
          } else if (response.code === 400) {
            this.errorMessage = "请求参数错误";
          } else if (response.code === 429) {
            this.errorMessage = "登录尝试次数过多，请稍后再试";
          } else {
            this.errorMessage = response.message || '登录失败，请稍后重试';
          }
        }
      } catch (error) {
        console.error('登录失败:', error);
        if (error.code === -1) {
          this.errorMessage = "网络错误，请检查服务器连接";
        } else {
          this.errorMessage = error.message || '登录失败，请稍后重试';
        }
      } finally {
        this.loading = false;
      }
    },

    showSuccessMessage(message) {
      // 使用浏览器原生alert或自定义提示
      alert(message);
    },

    showForgotPassword() {
      alert('忘记密码功能开发中...');
    },

    showComingSoon() {
      alert('该功能正在开发中，敬请期待！');
    }
  },
  mounted() {
    // 检查是否有记住的邮箱
    if (localStorage.getItem('rememberMe') === 'true') {
      const savedEmail = localStorage.getItem('userEmail');
      if (savedEmail) {
        this.loginForm.email = savedEmail;
        this.loginForm.remember = true;
      }
    }
  },
};
</script>

<style scoped>
.Login {
  min-height: 100vh;
  background-color: #0a0e17;
}

.bgcolor {
  background: linear-gradient(135deg, #082a78 0%, #0046db 100%);
  padding: 50px 0 100px;
}

.login-title {
  text-align: center;
  margin-bottom: 60px;
}

.login-title h2 {
  font-size: 40px;
  color: #fff;
  margin-bottom: 15px;
  background: linear-gradient(90deg, #0046db 0%, #0080ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.login-title p {
  color: rgba(255, 255, 255, 0.7);
  font-size: 18px;
}

/* 错误提示样式 */
.error-message {
  background: rgba(255, 107, 107, 0.1);
  border: 1px solid rgba(255, 107, 107, 0.3);
  border-radius: 30px;
  padding: 15px 20px;
  margin-bottom: 20px;
  color: #ff6b6b;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  animation: fadeIn 0.3s ease;
}

.error-message i {
  font-size: 16px;
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.login-container {
  display: flex;
  gap: 40px;
  max-width: 1200px;
  margin: 0 auto;
  align-items: stretch;
}

.login-left {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.login-right {
  flex: 1;
  max-width: 450px;
}

/* 左侧平台优势区域 */
.welcome-section {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 35px 30px;
  backdrop-filter: blur(10px);
  flex: 1;
}

.welcome-section h3 {
  font-size: 24px;
  color: #fff;
  margin-bottom: 20px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.welcome-section h3 i {
  color: #0046db;
}

.welcome-text {
  color: rgba(255, 255, 255, 0.7);
  line-height: 1.6;
  margin-bottom: 30px;
  font-size: 15px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
  margin-top: 25px;
}

.stat-item {
  text-align: center;
  padding: 20px 10px;
  background: rgba(0, 70, 219, 0.1);
  border: 1px solid rgba(0, 70, 219, 0.2);
  border-radius: 12px;
  transition: all 0.3s ease;
}

.stat-item:hover {
  transform: translateY(-3px);
  background: rgba(0, 70, 219, 0.2);
}

.stat-number {
  font-size: 22px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 5px;
  background: linear-gradient(90deg, #0080ff 0%, #00bfff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.stat-label {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.7);
  text-transform: uppercase;
  letter-spacing: 1px;
}

/* 平台功能列表 */
.platform-features {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 35px 30px;
  backdrop-filter: blur(10px);
  flex: 1;
}

.platform-features h4 {
  font-size: 20px;
  color: #fff;
  margin-bottom: 25px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.platform-features h4 i {
  color: #0046db;
}

.features-list {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 30px;
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
  transition: all 0.3s ease;
}

.feature-item:hover {
  background: rgba(0, 70, 219, 0.15);
  border-color: #0046db;
  transform: translateX(5px);
}

.feature-item i {
  color: #4caf50;
  font-size: 14px;
  min-width: 16px;
}

/* 右侧登录卡片 */
.login-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 40px;
  backdrop-filter: blur(10px);
  height: 100%;
  display: flex;
  flex-direction: column;
}

.login-card-header {
  text-align: center;
  margin-bottom: 40px;
}

.login-card-header h3 {
  font-size: 28px;
  color: #fff;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.login-card-header h3 i {
  color: #0046db;
}

.login-card-header p {
  color: rgba(255, 255, 255, 0.6);
  font-size: 15px;
}

.input-with-icon {
  position: relative;
  margin-bottom: 25px;
}

.input-with-icon i {
  position: absolute;
  left: 20px;
  top: 50%;
  transform: translateY(-50%);
  color: rgba(255, 255, 255, 0.6);
  font-size: 18px;
}

.input-with-icon input {
  width: 100%;
  padding: 16px 20px 16px 50px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 30px;
  color: #fff;
  font-size: 16px;
  transition: all 0.3s ease;
}

.input-with-icon input:focus {
  outline: none;
  border-color: #0046db;
  background: rgba(255, 255, 255, 0.08);
  box-shadow: 0 0 0 3px rgba(0, 70, 219, 0.1);
}

.input-with-icon input::placeholder {
  color: rgba(255, 255, 255, 0.4);
}

.input-with-icon input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.remember-me {
  display: flex;
  align-items: center;
  gap: 8px;
}

.remember-me input[type="checkbox"] {
  width: 18px;
  height: 18px;
  accent-color: #0046db;
}

.remember-me input[type="checkbox"]:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.remember-me label {
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
  cursor: pointer;
}

.forgot-password {
  color: #80d0ff;
  font-size: 14px;
  text-decoration: none;
  transition: color 0.3s ease;
  font-weight: 500;
}

.forgot-password:hover {
  color: #fff;
  text-decoration: underline;
}

.login-button {
  width: 100%;
  padding: 16px;
  background-color: #0046db;
  color: #fff;
  border: 1px solid #0046db;
  border-radius: 30px;
  font-size: 16px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  margin-bottom: 30px;
  position: relative;
}

.login-button:hover:not(:disabled) {
  background-color: #003db9;
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(0, 70, 219, 0.3);
}

.login-button:active:not(:disabled) {
  transform: translateY(0);
}

.login-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  background-color: #0046db;
}

.loading-spinner {
  display: inline-block;
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 50%;
  border-top-color: #fff;
  animation: spin 0.8s linear infinite;
  margin-left: 8px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.divider {
  position: relative;
  text-align: center;
  margin: 30px 0;
}

.divider::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  width: 100%;
  height: 1px;
  background: rgba(255, 255, 255, 0.1);
}

.divider span {
  display: inline-block;
  padding: 0 20px;
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.5);
  font-size: 14px;
  position: relative;
}

.social-login {
  display: flex;
  gap: 15px;
  margin-bottom: 30px;
}

.social-button {
  flex: 1;
  padding: 14px;
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 30px;
  background: rgba(255, 255, 255, 0.05);
  color: rgba(255, 255, 255, 0.8);
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.social-button:hover:not(:disabled) {
  background: rgba(255, 255, 255, 0.1);
  transform: translateY(-2px);
}

.social-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.social-button.wechat:hover:not(:disabled) {
  border-color: #07C160;
  color: #07C160;
}

.social-button.qq:hover:not(:disabled) {
  border-color: #12B7F5;
  color: #12B7F5;
}

/* 优化注册提示 */
.register-prompt {
  text-align: center;
  margin-top: auto;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
}

.prompt-text {
  color: rgba(255, 255, 255, 0.7);
  font-size: 14px;
}

.register-link {
  color: #80d0ff;
  text-decoration: none;
  font-weight: 600;
  margin-left: 8px;
  padding: 4px 12px;
  border-radius: 15px;
  transition: all 0.3s ease;
}

.register-link:hover {
  color: #fff;
  background: rgba(0, 112, 255, 0.2);
  text-decoration: none;
}

@media (max-width: 1000px) {
  .login-container {
    flex-direction: column;
    gap: 30px;
  }

  .login-right {
    max-width: 100%;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .features-list {
    grid-template-columns: 1fr;
  }

  .login-title h2 {
    font-size: 32px;
  }

  .login-title p {
    font-size: 16px;
  }

  .login-card {
    padding: 30px 20px;
  }

  .social-login {
    flex-direction: column;
  }

  .welcome-section,
  .platform-features {
    padding: 25px 20px;
  }
}

@media (max-width: 768px) {
  .bgcolor {
    padding: 30px 0 60px;
  }

  .login-title {
    margin-bottom: 40px;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>