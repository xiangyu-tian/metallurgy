<template>
  <Header></Header>
  <div class="Register">
    <div class="bgcolor">
      <div class="mb-nav">
        <div class="container">
          <p>
            当前位置： <router-link to="/">首页</router-link> >
            <span>用户注册</span>
          </p>
        </div>
      </div>
      <div class="container">
        <div class="register-title wow animate__animated animate__fadeInUp">
          <h2>创建账号</h2>
          <p>加入绿色低碳钢铁冶金全国重点实验室平台，开启智能材料研究之旅</p>
        </div>

        <div class="register-container wow animate__animated animate__fadeInUp">
          <!-- 错误提示 -->
          <div v-if="errorMessage" class="error-message">
            <i class="fas fa-exclamation-circle"></i> {{ errorMessage }}
          </div>

          <!-- 成功提示 -->
          <div v-if="successMessage" class="success-message">
            <i class="fas fa-check-circle"></i> {{ successMessage }}
          </div>

          <form class="register-form" @submit.prevent="handleRegister" v-if="!successMessage">
            <div class="form-sections">
              <div class="form-section">
                <h4 class="section-title">
                  <i class="fas fa-user"></i> 基本信息
                </h4>
                <div class="form-row">
                  <div class="form-group">
                    <label for="username">用户名 *</label>
                    <input
                        type="text"
                        id="username"
                        v-model="registerForm.username"
                        placeholder="请输入用户名（3-20位字母、数字或下划线）"
                        required
                        :disabled="loading"
                        @input="validateUsername"
                        autocomplete="username"
                    />
                    <p class="form-hint" :class="{ 'form-error': usernameError }">
                      {{ usernameError || '3-20位字母、数字或下划线' }}
                    </p>
                  </div>
                  <div class="form-group">
                    <label for="email">邮箱地址 *</label>
                    <input
                        type="email"
                        id="email"
                        v-model="registerForm.email"
                        placeholder="请输入邮箱地址"
                        required
                        :disabled="loading"
                        @input="validateEmail"
                        autocomplete="email"
                    />
                    <p class="form-hint" :class="{ 'form-error': emailError }">
                      {{ emailError || '请输入有效的邮箱地址' }}
                    </p>
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label for="realName">真实姓名（可选）</label>
                    <input
                        type="text"
                        id="realName"
                        v-model="registerForm.realName"
                        placeholder="请输入真实姓名"
                        :disabled="loading"
                        autocomplete="name"
                    />
                    <p class="form-hint">建议填写真实姓名以便识别</p>
                  </div>
                  <div class="form-group">
                    <label for="organization">所属单位（可选）</label>
                    <input
                        type="text"
                        id="organization"
                        v-model="registerForm.organization"
                        placeholder="请输入单位名称"
                        :disabled="loading"
                        autocomplete="organization"
                    />
                    <p class="form-hint">例如：绿色低碳钢铁冶金全国重点实验室</p>
                  </div>
                </div>
              </div>

              <div class="form-section">
                <h4 class="section-title">
                  <i class="fas fa-shield-alt"></i> 安全设置
                </h4>
                <div class="form-row">
                  <div class="form-group">
                    <label for="password">密码 *</label>
                    <input
                        type="password"
                        id="password"
                        v-model="registerForm.password"
                        placeholder="请设置密码（至少8位）"
                        required
                        :disabled="loading"
                        @input="checkPasswordStrength"
                        autocomplete="new-password"
                    />
                    <div class="password-strength">
                      <div class="strength-bar" :class="strengthClass"></div>
                    </div>
                    <p class="form-hint">至少8位，建议包含字母、数字和特殊字符</p>
                  </div>
                  <div class="form-group">
                    <label for="confirmPassword">确认密码 *</label>
                    <input
                        type="password"
                        id="confirmPassword"
                        v-model="registerForm.confirmPassword"
                        placeholder="请再次输入密码"
                        required
                        :disabled="loading"
                        @input="checkPasswordMatch"
                        autocomplete="new-password"
                    />
                    <p v-if="passwordMismatch" class="form-error">两次输入的密码不一致</p>
                  </div>
                </div>
              </div>
            </div>

            <div class="form-agreement">
              <div class="agreement-content">
                <input
                    type="checkbox"
                    id="agreement"
                    v-model="registerForm.agreed"
                    required
                    :disabled="loading"
                />
                <label for="agreement">
                  <i class="fas fa-file-contract"></i>
                  <span class="agreement-text">
                    我已阅读并同意
                    <a href="/agreement" class="agreement-link" target="_blank">《用户服务协议》</a>和
                    <a href="/privacy" class="agreement-link" target="_blank">《隐私政策》</a>
                  </span>
                </label>
              </div>
            </div>

            <button
                type="submit"
                class="register-button"
                :disabled="loading || !isFormValid"
            >
              <i class="fas fa-user-plus"></i>
              <span>{{ loading ? '注册中...' : '注册账号' }}</span>
              <span v-if="loading" class="loading-spinner"></span>
            </button>

            <div class="login-prompt">
              <i class="fas fa-sign-in-alt prompt-icon"></i>
              <span class="prompt-text">已有账号？</span>
              <router-link to="/login" class="login-link">立即登录</router-link>
            </div>
          </form>
        </div>

        <div class="register-features wow animate__animated animate__fadeInUp">
          <h3><i class="fas fa-star"></i> 平台特色功能</h3>
          <div class="features-grid">
            <div class="feature-card">
              <div class="feature-icon">
                <i class="fas fa-database"></i>
              </div>
              <h4>海量冶金数据库</h4>
              <p>超过540,000种材料的完整数据，涵盖化学成分、机械性能等</p>
            </div>
            <div class="feature-card">
              <div class="feature-icon">
                <i class="fas fa-calculator"></i>
              </div>
              <h4>专业计算工具</h4>
              <p>冶金流体力学、热力学计算，转炉CFD结构化网格快速生成</p>
            </div>
            <div class="feature-card">
              <div class="feature-icon">
                <i class="fas fa-brain"></i>
              </div>
              <h4>AI智能分析</h4>
              <p>人工智能材料性能预测，专利算法，光谱仪集成</p>
            </div>
            <div class="feature-card">
              <div class="feature-icon">
                <i class="fas fa-leaf"></i>
              </div>
              <h4>绿色低碳</h4>
              <p>碳排放核算，资源循环利用，推动钢铁冶金行业可持续发展</p>
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
  name: "UserRegister",
  components: {
    Header,
    Footer,
  },
  data() {
    return {
      registerForm: {
        username: "",
        email: "",
        realName: "",
        organization: "",
        password: "",
        confirmPassword: "",
        agreed: false,
      },
      loading: false,
      errorMessage: "",
      successMessage: "",
      strengthClass: "",
      passwordMismatch: false,
      usernameError: "",
      emailError: "",
    };
  },
  computed: {
    isFormValid() {
      return (
          this.registerForm.username &&
          !this.usernameError &&
          this.registerForm.email &&
          !this.emailError &&
          this.registerForm.password &&
          this.registerForm.confirmPassword &&
          !this.passwordMismatch &&
          this.registerForm.agreed &&
          this.strengthClass === 'strength-strong'
      );
    }
  },
  methods: {
    validateUsername() {
      const username = this.registerForm.username.trim();
      if (username.length === 0) {
        this.usernameError = "用户名不能为空";
        return;
      }
      if (username.length < 3 || username.length > 20) {
        this.usernameError = "用户名长度应为3-20位";
        return;
      }
      const usernameRegex = /^[a-zA-Z0-9_]+$/;
      if (!usernameRegex.test(username)) {
        this.usernameError = "只能包含字母、数字和下划线";
        return;
      }
      this.usernameError = "";
    },

    validateEmail() {
      const email = this.registerForm.email.trim();
      const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
      if (!emailRegex.test(email)) {
        this.emailError = "请输入有效的邮箱地址";
        return;
      }
      this.emailError = "";
    },

    checkPasswordStrength() {
      const password = this.registerForm.password;
      let strength = 0;
      if (password.length >= 8) strength++;
      if (/\d/.test(password)) strength++;
      if (/[a-z]/.test(password)) strength++;
      if (/[A-Z]/.test(password)) strength++;
      if (/[^A-Za-z0-9]/.test(password)) strength++;

      if (strength >= 4) {
        this.strengthClass = "strength-strong";
      } else if (strength >= 2) {
        this.strengthClass = "strength-medium";
      } else if (strength >= 1) {
        this.strengthClass = "strength-weak";
      } else {
        this.strengthClass = "";
      }
    },

    checkPasswordMatch() {
      this.passwordMismatch =
          this.registerForm.confirmPassword &&
          this.registerForm.password !== this.registerForm.confirmPassword;
    },

    async handleRegister() {
      // 重置错误状态
      this.errorMessage = "";
      this.successMessage = "";

      // 表单验证
      this.validateUsername();
      this.validateEmail();
      this.checkPasswordMatch();

      if (this.usernameError || this.emailError || this.passwordMismatch) {
        return;
      }

      if (!this.registerForm.agreed) {
        this.errorMessage = "请阅读并同意用户协议和隐私政策";
        return;
      }

      if (this.strengthClass !== 'strength-strong') {
        this.errorMessage = "密码强度不足，请设置更复杂的密码";
        return;
      }

      this.loading = true;

      try {
        // 使用 this.$axios 发送请求
        const response = await this.$axios.post('/auth/register', {
          username: this.registerForm.username,
          email: this.registerForm.email,
          password: this.registerForm.password,
          realName: this.registerForm.realName || '',
          organization: this.registerForm.organization || ''
        });

        if (response.code === 200) {
          // 显示成功消息
          this.successMessage = '注册成功！3秒后将跳转到登录页面...';

          // 3秒后跳转到登录页面
          setTimeout(() => {
            this.$router.push('/login');
          }, 3000);
        } else {
          // 处理各种错误情况
          if (response.code === 400) {
            if (response.message.includes('用户名')) {
              this.errorMessage = "用户名已存在或格式不正确";
            } else if (response.message.includes('邮箱')) {
              this.errorMessage = "邮箱已注册或格式不正确";
            } else {
              this.errorMessage = response.message || "注册失败，请检查输入信息";
            }
          } else if (response.code === 409) {
            this.errorMessage = "用户名或邮箱已被注册";
          } else {
            this.errorMessage = response.message || '注册失败，请稍后重试';
          }
        }
      } catch (error) {
        console.error('注册失败:', error);
        if (error.code === -1) {
          this.errorMessage = "网络错误，请检查服务器连接";
        } else {
          this.errorMessage = error.message || '注册失败，请稍后重试';
        }
      } finally {
        this.loading = false;
      }
    }
  }
};
</script>

<style scoped>
.Register {
  min-height: 100vh;
}

.bgcolor {
  background: linear-gradient(135deg, #082a78 0%, #0046db 100%);
  padding: 50px 0 100px;
}

.register-title {
  text-align: center;
  margin-bottom: 60px;
}

.register-title h2 {
  font-size: 40px;
  color: #fff;
  margin-bottom: 15px;
  background: linear-gradient(90deg, #0046db 0%, #0080ff 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}

.register-title p {
  color: rgba(255, 255, 255, 0.7);
  font-size: 18px;
}

.register-container {
  max-width: 900px;
  margin: 0 auto 80px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 50px;
  backdrop-filter: blur(10px);
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

.success-message {
  background: rgba(76, 175, 80, 0.1);
  border: 1px solid rgba(76, 175, 80, 0.3);
  border-radius: 30px;
  padding: 15px 20px;
  margin-bottom: 20px;
  color: #4caf50;
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  animation: fadeIn 0.3s ease;
}

.error-message i,
.success-message i {
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

.form-sections {
  margin-bottom: 30px;
}

.form-section {
  margin-bottom: 40px;
  padding-bottom: 30px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.section-title {
  font-size: 20px;
  color: #fff;
  margin-bottom: 25px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.section-title i {
  color: #0046db;
  width: 24px;
}

.form-row {
  display: flex;
  gap: 30px;
  margin-bottom: 20px;
}

.form-group {
  flex: 1;
}

.form-group label {
  display: block;
  color: rgba(255, 255, 255, 0.9);
  margin-bottom: 8px;
  font-size: 14px;
  font-weight: 500;
}

.form-group input {
  width: 100%;
  padding: 15px 20px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.2);
  border-radius: 30px;
  color: #fff;
  font-size: 16px;
  transition: all 0.3s ease;
}

.form-group input:focus {
  outline: none;
  border-color: #0046db;
  background: rgba(255, 255, 255, 0.08);
  box-shadow: 0 0 0 3px rgba(0, 70, 219, 0.1);
}

.form-group input:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.form-hint {
  margin-top: 8px;
  color: rgba(255, 255, 255, 0.5);
  font-size: 12px;
}

.form-error {
  margin-top: 8px;
  color: #ff6b6b !important;
  font-size: 12px;
  font-weight: 500;
}

.password-strength {
  height: 6px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 3px;
  margin-top: 10px;
  overflow: hidden;
}

.strength-bar {
  height: 100%;
  width: 0%;
  transition: width 0.3s ease;
}

.strength-weak {
  width: 33%;
  background: #ff6b6b;
}

.strength-medium {
  width: 66%;
  background: #ffa726;
}

.strength-strong {
  width: 100%;
  background: #4caf50;
}

/* 优化协议区域 */
.form-agreement {
  margin: 40px 0;
  padding: 20px;
  background: rgba(0, 70, 219, 0.1);
  border: 1px solid rgba(0, 70, 219, 0.2);
  border-radius: 15px;
}

.agreement-content {
  display: flex;
  align-items: flex-start;
  gap: 15px;
}

.agreement-content input[type="checkbox"] {
  margin-top: 3px;
  accent-color: #0046db;
  width: 18px;
  height: 18px;
  flex-shrink: 0;
}

.agreement-content input[type="checkbox"]:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.agreement-content label {
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
  line-height: 1.6;
  display: flex;
  align-items: center;
  gap: 10px;
  cursor: pointer;
}

.agreement-text {
  display: inline;
}

.agreement-link {
  color: #80d0ff;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.3s ease;
  padding: 0 2px;
}

.agreement-link:hover {
  color: #fff;
  text-decoration: underline;
  background: rgba(0, 112, 255, 0.2);
  border-radius: 3px;
}

/* 注册按钮 */
.register-button {
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
  margin-bottom: 30px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  position: relative;
}

.register-button:hover:not(:disabled) {
  background-color: #003db9;
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(0, 70, 219, 0.3);
}

.register-button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  background-color: #0046db;
}

.register-button i {
  font-size: 18px;
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

/* 优化登录提示 */
.login-prompt {
  text-align: center;
  color: rgba(255, 255, 255, 0.9);
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  padding: 15px;
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 30px;
}

.prompt-icon {
  color: #80d0ff !important;
}

.prompt-text {
  color: rgba(255, 255, 255, 0.7);
}

.login-link {
  color: #80d0ff;
  text-decoration: none;
  font-weight: 600;
  transition: all 0.3s ease;
  padding: 2px 8px;
  border-radius: 15px;
}

.login-link:hover {
  color: #fff;
  background: rgba(0, 112, 255, 0.2);
  text-decoration: none;
}

/* 平台特色功能部分 */
.register-features {
  max-width: 1200px;
  margin: 0 auto;
}

.register-features h3 {
  font-size: 28px;
  color: #fff;
  text-align: center;
  margin-bottom: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
}

.register-features h3 i {
  color: #0046db;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 25px;
}

.feature-card {
  background: rgba(255, 255, 255, 0.05);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 15px;
  padding: 25px;
  text-align: center;
  transition: all 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-5px);
  background: rgba(255, 255, 255, 0.08);
  border-color: #0046db;
}

.feature-icon {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, #0046db 0%, #0080ff 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
}

.feature-icon i {
  font-size: 24px;
  color: #fff;
}

.feature-card h4 {
  font-size: 18px;
  color: #fff;
  margin-bottom: 10px;
}

.feature-card p {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.6);
  line-height: 1.5;
}

@media (max-width: 1000px) {
  .register-container {
    padding: 30px 20px;
    margin-bottom: 60px;
  }

  .register-title h2 {
    font-size: 32px;
  }

  .form-row {
    flex-direction: column;
    gap: 20px;
  }

  .features-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .agreement-content {
    align-items: flex-start;
  }

  .agreement-content label {
    align-items: flex-start;
  }
}

@media (max-width: 768px) {
  .bgcolor {
    padding: 30px 0 60px;
  }

  .register-title {
    margin-bottom: 40px;
  }

  .register-title h2 {
    font-size: 28px;
  }

  .register-title p {
    font-size: 16px;
  }

  .features-grid {
    grid-template-columns: 1fr;
  }

  .register-features h3 {
    font-size: 24px;
  }

  .login-prompt {
    flex-direction: column;
    gap: 8px;
  }
}
</style>