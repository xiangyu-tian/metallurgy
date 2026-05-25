<template>
  <div class="profile-container">
    <!-- 页面标题 -->
    <div class="profile-header">
      <h1><i class="fas fa-user-circle"></i> 个人中心</h1>
      <div class="user-welcome">
        欢迎回来，<span class="user-name">{{ displayName }}</span>
        <span v-if="userRole" class="user-role-badge" :class="userRole">
          {{ userRole === 'admin' ? '管理员' : '用户' }}
        </span>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <div v-else class="profile-content">
      <!-- 左侧：导航菜单 -->
      <div class="profile-sidebar">
        <nav class="sidebar-nav" :class="{ show: showMobileMenu }">
          <!-- 基础菜单项 -->
          <a :class="['nav-item', { active: activeTab === 'profile' }]"
             @click="switchTab('profile')">
            <i class="fas fa-user"></i>
            <span>我的资料</span>
          </a>
          <a :class="['nav-item', { active: activeTab === 'security' }]"
             @click="switchTab('security')">
            <i class="fas fa-lock"></i>
            <span>安全设置</span>
          </a>

          <!-- 管理员专属菜单项 -->
          <div v-if="isAdmin" class="admin-section">
            <div class="section-title">
              <i class="fas fa-crown"></i>
              <span>管理员功能</span>
            </div>

            <a :class="['nav-item', { active: activeTab === 'users' }]"
               @click="switchTab('users')">
              <i class="fas fa-users-cog"></i>
              <span>用户管理</span>
              <span v-if="totalUsers > 0" class="user-count">{{ totalUsers }}</span>
            </a>

            <!-- 新增：模型管理 -->
            <a :class="['nav-item', { active: activeTab === 'models' }]"
               @click="switchTab('models')">
              <i class="fas fa-brain"></i>
              <span>模型管理</span>
              <span class="feature-badge">新</span>
            </a>

            <!-- 新增：智能体管理 -->
            <a :class="['nav-item', { active: activeTab === 'agents' }]"
               @click="switchTab('agents')">
              <i class="fas fa-robot"></i>
              <span>智能体管理</span>
              <span class="feature-badge">AI</span>
            </a>

            <!-- 新增：知识库管理 -->
            <a :class="['nav-item', { active: activeTab === 'knowledge' }]"
               @click="switchTab('knowledge')">
              <i class="fas fa-book"></i>
              <span>知识库管理</span>
              <span class="feature-badge">知识</span>
            </a>
          </div>
        </nav>

        <!-- 移动端菜单按钮 -->
        <button class="mobile-menu-btn" @click="toggleMobileMenu">
          <i class="fas fa-bars"></i>
        </button>
      </div>

      <!-- 右侧：内容区域 -->
      <div class="profile-main">
        <!-- 我的资料 -->
        <div v-if="activeTab === 'profile'" class="tab-content">
          <div class="section-header">
            <h2><i class="fas fa-id-card"></i> 我的资料</h2>
            <p class="section-subtitle">管理您的个人信息</p>
          </div>

          <div class="profile-form-container">
            <form @submit.prevent="updateProfile">
              <div class="form-group">
                <label for="username">
                  <i class="fas fa-user-tag"></i> 用户名
                </label>
                <input type="text" id="username" v-model="userForm.username"
                       :disabled="isSubmitting" required>
                <div class="form-hint">用于登录的用户名，3-20位字符</div>
              </div>

              <div class="form-group">
                <label for="email">
                  <i class="fas fa-envelope"></i> 邮箱
                </label>
                <input type="email" id="email" v-model="userForm.email"
                       :disabled="isSubmitting" required>
                <div class="form-hint">用于登录和接收通知</div>
              </div>

              <div class="form-group">
                <label for="realName">
                  <i class="fas fa-signature"></i> 真实姓名
                </label>
                <input type="text" id="realName" v-model="userForm.realName"
                       :disabled="isSubmitting">
                <div class="form-hint">可选，建议填写真实姓名</div>
              </div>

              <div class="form-group">
                <label for="organization">
                  <i class="fas fa-building"></i> 单位/组织
                </label>
                <input type="text" id="organization" v-model="userForm.organization"
                       :disabled="isSubmitting">
                <div class="form-hint">可选，填写您所在的单位</div>
              </div>

              <div class="form-actions">
                <button type="button" class="btn-cancel" @click="resetProfileForm"
                        :disabled="isSubmitting">
                  取消
                </button>
                <button type="submit" class="btn-save" :disabled="isSubmitting || !isProfileFormChanged">
                  <i v-if="isSubmitting" class="fas fa-spinner fa-spin"></i>
                  {{ isSubmitting ? '保存中...' : '保存更改' }}
                </button>
              </div>
            </form>
          </div>
        </div>

        <!-- 安全设置 -->
        <div v-else-if="activeTab === 'security'" class="tab-content">
          <div class="section-header">
            <h2><i class="fas fa-shield-alt"></i> 安全设置</h2>
            <p class="section-subtitle">修改登录密码</p>
          </div>

          <div class="security-form-container">
            <form @submit.prevent="changePassword">
              <div class="form-group">
                <label for="currentPassword">
                  <i class="fas fa-key"></i> 当前密码
                </label>
                <input :type="showCurrentPassword ? 'text' : 'password'"
                       id="currentPassword" v-model="passwordForm.currentPassword"
                       :disabled="isChangingPassword" required>
                <span class="password-toggle" @click="showCurrentPassword = !showCurrentPassword">
                  <i :class="showCurrentPassword ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
                </span>
              </div>

              <div class="form-group">
                <label for="newPassword">
                  <i class="fas fa-lock"></i> 新密码
                </label>
                <input :type="showNewPassword ? 'text' : 'password'"
                       id="newPassword" v-model="passwordForm.newPassword"
                       :disabled="isChangingPassword" required>
                <span class="password-toggle" @click="showNewPassword = !showNewPassword">
                  <i :class="showNewPassword ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
                </span>
                <div class="form-hint">至少8位字符，建议包含字母、数字和符号</div>
                <div class="password-strength" :class="passwordStrength">
                  密码强度: {{ passwordStrengthText }}
                </div>
              </div>

              <div class="form-group">
                <label for="confirmPassword">
                  <i class="fas fa-lock"></i> 确认新密码
                </label>
                <input :type="showConfirmPassword ? 'text' : 'password'"
                       id="confirmPassword" v-model="passwordForm.confirmPassword"
                       :disabled="isChangingPassword" required>
                <span class="password-toggle" @click="showConfirmPassword = !showConfirmPassword">
                  <i :class="showConfirmPassword ? 'fas fa-eye-slash' : 'fas fa-eye'"></i>
                </span>
                <div class="form-hint" :class="{ error: !passwordsMatch && passwordForm.confirmPassword }">
                  {{ passwordsMatch ? '密码匹配' : '两次输入的密码不一致' }}
                </div>
              </div>

              <div class="form-actions">
                <button type="button" class="btn-cancel" @click="resetPasswordForm"
                        :disabled="isChangingPassword">
                  取消
                </button>
                <button type="submit" class="btn-save"
                        :disabled="isChangingPassword || !isPasswordFormValid">
                  <i v-if="isChangingPassword" class="fas fa-spinner fa-spin"></i>
                  {{ isChangingPassword ? '修改中...' : '修改密码' }}
                </button>
              </div>
            </form>
          </div>
        </div>

        <!-- 用户管理（仅管理员） -->
        <div v-else-if="activeTab === 'users' && isAdmin" class="tab-content">
          <div class="section-header">
            <h2><i class="fas fa-users"></i> 用户管理</h2>
            <div class="header-actions">
              <div class="search-box">
                <i class="fas fa-search"></i>
                <input type="text" v-model="searchQuery" placeholder="搜索用户名、邮箱或真实姓名..."
                       @input="debouncedSearch" :disabled="loadingUsers">
              </div>

              <button v-if="selectedUsers.length > 0" class="btn-delete-batch"
                      @click="confirmBatchDelete" :disabled="loadingUsers">
                <i class="fas fa-trash"></i> 批量删除 ({{ selectedUsers.length }})
              </button>
            </div>
          </div>

          <!-- 用户表格 -->
          <div class="users-table-container">
            <div class="table-responsive">
              <table class="users-table">
                <thead>
                <tr>
                  <th class="select-column">
                    <input type="checkbox" v-model="selectAll" @change="toggleSelectAll">
                  </th>
                  <th>ID</th>
                  <th>用户名</th>
                  <th>邮箱</th>
                  <th>真实姓名</th>
                  <th>角色</th>
                  <th>状态</th>
                  <th>创建时间</th>
                  <th>最后登录</th>
                  <th>操作</th>
                </tr>
                </thead>
                <tbody>
                <tr v-if="loadingUsers">
                  <td colspan="10" class="loading-row">
                    <div class="table-loading">
                      <div class="spinner"></div>
                      <span>加载用户数据...</span>
                    </div>
                  </td>
                </tr>
                <tr v-else-if="users.length === 0">
                  <td colspan="10" class="empty-row">
                    <i class="fas fa-users-slash"></i>
                    <p>暂无用户数据</p>
                  </td>
                </tr>
                <tr v-else v-for="user in users" :key="user.id"
                    :class="{ 'current-user': user.id === currentUserId }">
                  <td class="select-column">
                    <input type="checkbox" :value="user.id" v-model="selectedUsers"
                           :disabled="user.id === currentUserId">
                  </td>
                  <td class="user-id">{{ user.id }}</td>
                  <td class="username">{{ user.username }}</td>
                  <td class="email">{{ user.email }}</td>
                  <td class="real-name">{{ user.real_name || '-' }}</td>
                  <td class="user-role">
                      <span class="role-badge" :class="user.role">
                        {{ user.role === 'admin' ? '管理员' : '用户' }}
                      </span>
                  </td>
                  <td class="user-status">
                      <span class="status-badge" :class="user.account_status">
                        {{ user.account_status === 'active' ? '活跃' : '禁用' }}
                      </span>
                  </td>
                  <td class="created-at">{{ formatDate(user.created_at) }}</td>
                  <td class="last-login">{{ user.last_login_at ? formatDate(user.last_login_at) : '从未登录' }}</td>
                  <td class="actions">
                    <button class="btn-edit" @click="editUser(user)"
                            :disabled="user.id === currentUserId">
                      <i class="fas fa-edit"></i> 编辑
                    </button>
                    <button class="btn-delete" @click="confirmDeleteUser(user)"
                            :disabled="user.id === currentUserId">
                      <i class="fas fa-trash"></i> 删除
                    </button>
                  </td>
                </tr>
                </tbody>
              </table>
            </div>

            <!-- 分页 -->
            <div v-if="totalPages > 1" class="pagination-container">
              <div class="pagination-info">
                显示 {{ startItem }}-{{ endItem }} 条，共 {{ totalItems }} 条
              </div>
              <div class="pagination-controls">
                <button class="pagination-btn" :disabled="currentPage === 1"
                        @click="changePage(currentPage - 1)">
                  <i class="fas fa-chevron-left"></i> 上一页
                </button>

                <div class="page-numbers">
                  <button v-for="page in pageNumbers" :key="page"
                          :class="['page-btn', { active: page === currentPage }]"
                          @click="changePage(page)"
                          :disabled="page === '...'">
                    {{ page }}
                  </button>
                </div>

                <button class="pagination-btn" :disabled="currentPage === totalPages"
                        @click="changePage(currentPage + 1)">
                  下一页 <i class="fas fa-chevron-right"></i>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 模型管理（仅管理员） -->
        <div v-else-if="activeTab === 'models' && isAdmin" class="tab-content">
          <div class="section-header">
            <h2><i class="fas fa-brain"></i> 模型管理</h2>
            <p class="section-subtitle">管理AI模型配置与参数</p>
          </div>

          <div class="ai-management-container">
            <!-- 模型状态概览 -->
            <div class="stats-overview">
              <div class="stat-card">
                <div class="stat-icon">
                  <i class="fas fa-check-circle"></i>
                </div>
                <div class="stat-content">
                  <h3>已启用模型</h3>
                  <p class="stat-value">2</p>
                  <p class="stat-desc">当前可用的AI模型</p>
                </div>
              </div>
              <div class="stat-card">
                <div class="stat-icon">
                  <i class="fas fa-bolt"></i>
                </div>
                <div class="stat-content">
                  <h3>总调用次数</h3>
                  <p class="stat-value">1,245</p>
                  <p class="stat-desc">本月API调用</p>
                </div>
              </div>
              <div class="stat-card">
                <div class="stat-icon">
                  <i class="fas fa-history"></i>
                </div>
                <div class="stat-content">
                  <h3>平均响应时间</h3>
                  <p class="stat-value">1.2s</p>
                  <p class="stat-desc">模型平均响应</p>
                </div>
              </div>
            </div>

            <!-- 模型配置 -->
            <div class="model-config-section">
              <h3>模型配置</h3>
              <div class="model-list">
                <div class="model-card">
                  <div class="model-header">
                    <div class="model-info">
                      <i class="fas fa-robot"></i>
                      <div>
                        <h4>通义千问（Qwen）</h4>
                        <span class="model-tag active">已启用</span>
                        <span class="model-tag api-key">API集成</span>
                      </div>
                    </div>
                    <div class="model-actions">
                      <button class="btn-action btn-edit" @click="editModel('qwen')">
                        <i class="fas fa-cog"></i> 配置
                      </button>
                    </div>
                  </div>
                  <div class="model-details">
                    <p><i class="fas fa-key"></i> API密钥状态：<span class="status-success">已验证</span></p>
                    <p><i class="fas fa-sliders-h"></i> 模型参数：温度 0.8，Top-p 0.9</p>
                    <p><i class="fas fa-history"></i> 最后更新：2024-01-10</p>
                  </div>
                </div>

                <div class="model-card">
                  <div class="model-header">
                    <div class="model-info">
                      <i class="fas fa-brain"></i>
                      <div>
                        <h4>本地模型（测试）</h4>
                        <span class="model-tag warning">测试中</span>
                        <span class="model-tag local">本地部署</span>
                      </div>
                    </div>
                    <div class="model-actions">
                      <button class="btn-action btn-test" @click="testModel('local')">
                        <i class="fas fa-play"></i> 测试
                      </button>
                    </div>
                  </div>
                  <div class="model-details">
                    <p><i class="fas fa-server"></i> 部署状态：<span class="status-warning">运行中</span></p>
                    <p><i class="fas fa-microchip"></i> 内存占用：4.2GB</p>
                    <p><i class="fas fa-clock"></i> 启动时间：2024-01-12 08:30</p>
                  </div>
                </div>
              </div>

              <div class="add-model-section">
                <h4>添加新模型</h4>
                <div class="add-model-options">
                  <button class="add-option" @click="showAddModal('api')">
                    <i class="fas fa-cloud"></i>
                    <span>API模型</span>
                    <small>连接第三方AI服务</small>
                  </button>
                  <button class="add-option" @click="showAddModal('local')">
                    <i class="fas fa-server"></i>
                    <span>本地模型</span>
                    <small>部署本地AI模型</small>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 智能体管理（仅管理员） -->
        <div v-else-if="activeTab === 'agents' && isAdmin" class="tab-content">
          <div class="section-header">
            <h2><i class="fas fa-robot"></i> 智能体管理</h2>
            <p class="section-subtitle">配置和管理AI智能体</p>
          </div>

          <div class="ai-management-container">
            <!-- 智能体列表 -->
            <div class="agents-list">
              <div class="agent-card">
                <div class="agent-header">
                  <div class="agent-avatar">
                    <i class="fas fa-industry"></i>
                  </div>
                  <div class="agent-info">
                    <h3>冶金专家助手</h3>
                    <p class="agent-desc">专注于冶金领域的智能问答助手</p>
                    <div class="agent-tags">
                      <span class="tag">冶金</span>
                      <span class="tag">材料科学</span>
                      <span class="tag">碳中和</span>
                    </div>
                  </div>
                  <div class="agent-status">
                    <span class="status-badge active">运行中</span>
                    <p class="stat">今日调用：56次</p>
                  </div>
                </div>
                <div class="agent-actions">
                  <button class="btn-action btn-edit" @click="editAgent('metallurgy')">
                    <i class="fas fa-edit"></i> 编辑
                  </button>
                  <button class="btn-action btn-config" @click="configureAgent('metallurgy')">
                    <i class="fas fa-cog"></i> 配置
                  </button>
                  <button class="btn-action btn-test" @click="testAgent('metallurgy')">
                    <i class="fas fa-play"></i> 测试
                  </button>
                </div>
              </div>

              <div class="agent-card">
                <div class="agent-header">
                  <div class="agent-avatar">
                    <i class="fas fa-calculator"></i>
                  </div>
                  <div class="agent-info">
                    <h3>计算助手</h3>
                    <p class="agent-desc">冶金计算与数据分析助手</p>
                    <div class="agent-tags">
                      <span class="tag">计算</span>
                      <span class="tag">数据分析</span>
                      <span class="tag">公式</span>
                    </div>
                  </div>
                  <div class="agent-status">
                    <span class="status-badge active">运行中</span>
                    <p class="stat">今日调用：32次</p>
                  </div>
                </div>
                <div class="agent-actions">
                  <button class="btn-action btn-edit" @click="editAgent('calculator')">
                    <i class="fas fa-edit"></i> 编辑
                  </button>
                  <button class="btn-action btn-config" @click="configureAgent('calculator')">
                    <i class="fas fa-cog"></i> 配置
                  </button>
                  <button class="btn-action btn-test" @click="testAgent('calculator')">
                    <i class="fas fa-play"></i> 测试
                  </button>
                </div>
              </div>
            </div>

            <!-- 创建新智能体 -->
            <div class="create-agent-section">
              <h3>创建新智能体</h3>
              <div class="create-form">
                <div class="form-group">
                  <label for="agent-name">智能体名称</label>
                  <input type="text" id="agent-name" placeholder="例如：工艺优化助手" v-model="newAgent.name">
                </div>
                <div class="form-group">
                  <label for="agent-desc">描述</label>
                  <textarea id="agent-desc" placeholder="描述智能体的功能和用途" v-model="newAgent.description"></textarea>
                </div>
                <div class="form-group">
                  <label for="agent-model">选择模型</label>
                  <select id="agent-model" v-model="newAgent.model">
                    <option value="qwen">通义千问 (Qwen)</option>
                    <option value="local">本地模型</option>
                  </select>
                </div>
                <div class="form-group">
                  <label>功能标签</label>
                  <div class="tag-selection">
                    <span class="tag-selectable" :class="{ selected: newAgent.tags.includes('冶金') }" @click="toggleTag('冶金')">冶金</span>
                    <span class="tag-selectable" :class="{ selected: newAgent.tags.includes('材料') }" @click="toggleTag('材料')">材料</span>
                    <span class="tag-selectable" :class="{ selected: newAgent.tags.includes('计算') }" @click="toggleTag('计算')">计算</span>
                    <span class="tag-selectable" :class="{ selected: newAgent.tags.includes('分析') }" @click="toggleTag('分析')">分析</span>
                    <span class="tag-selectable" :class="{ selected: newAgent.tags.includes('优化') }" @click="toggleTag('优化')">优化</span>
                  </div>
                </div>
                <div class="form-actions">
                  <button class="btn-cancel" @click="resetNewAgent">取消</button>
                  <button class="btn-save" @click="createAgent">创建智能体</button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 知识库管理（仅管理员） -->
        <div v-else-if="activeTab === 'knowledge' && isAdmin" class="tab-content">
          <div class="section-header">
            <h2><i class="fas fa-book"></i> 知识库管理</h2>
            <p class="section-subtitle">管理冶金领域知识库文档</p>
          </div>

          <div class="ai-management-container">
            <!-- 知识库统计 -->
            <div class="stats-overview">
              <div class="stat-card">
                <div class="stat-icon">
                  <i class="fas fa-file-alt"></i>
                </div>
                <div class="stat-content">
                  <h3>文档数量</h3>
                  <p class="stat-value">147</p>
                  <p class="stat-desc">知识库文档</p>
                </div>
              </div>
              <div class="stat-card">
                <div class="stat-icon">
                  <i class="fas fa-database"></i>
                </div>
                <div class="stat-content">
                  <h3>向量库大小</h3>
                  <p class="stat-value">2.3GB</p>
                  <p class="stat-desc">向量数据存储</p>
                </div>
              </div>
              <div class="stat-card">
                <div class="stat-icon">
                  <i class="fas fa-search"></i>
                </div>
                <div class="stat-content">
                  <h3>搜索命中</h3>
                  <p class="stat-value">3,892</p>
                  <p class="stat-desc">本月搜索次数</p>
                </div>
              </div>
            </div>

            <!-- 知识库管理 -->
            <div class="knowledge-management">
              <div class="knowledge-header">
                <h3>知识库文档</h3>
                <div class="knowledge-actions">
                  <button class="btn-action btn-upload" @click="showUploadModal">
                    <i class="fas fa-upload"></i> 上传文档
                  </button>
                  <button class="btn-action btn-sync" @click="syncKnowledgeBase">
                    <i class="fas fa-sync-alt"></i> 同步向量库
                  </button>
                </div>
              </div>

              <!-- 文档列表 -->
              <div class="documents-list">
                <div class="document-item">
                  <div class="doc-icon">
                    <i class="fas fa-file-pdf"></i>
                  </div>
                  <div class="doc-info">
                    <h4>冶金工艺手册.pdf</h4>
                    <p class="doc-meta">
                      <span><i class="fas fa-calendar"></i> 2024-01-10</span>
                      <span><i class="fas fa-weight"></i> 5.2MB</span>
                      <span><i class="fas fa-hashtag"></i> 工艺、手册</span>
                    </p>
                    <p class="doc-status">
                      <i class="fas fa-check-circle status-success"></i> 已向量化
                    </p>
                  </div>
                  <div class="doc-actions">
                    <button class="btn-action btn-view" title="预览">
                      <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn-action btn-download" title="下载">
                      <i class="fas fa-download"></i>
                    </button>
                    <button class="btn-action btn-delete" title="删除">
                      <i class="fas fa-trash"></i>
                    </button>
                  </div>
                </div>

                <div class="document-item">
                  <div class="doc-icon">
                    <i class="fas fa-file-word"></i>
                  </div>
                  <div class="doc-info">
                    <h4>钢铁材料标准.docx</h4>
                    <p class="doc-meta">
                      <span><i class="fas fa-calendar"></i> 2024-01-08</span>
                      <span><i class="fas fa-weight"></i> 3.1MB</span>
                      <span><i class="fas fa-hashtag"></i> 标准、材料</span>
                    </p>
                    <p class="doc-status">
                      <i class="fas fa-check-circle status-success"></i> 已向量化
                    </p>
                  </div>
                  <div class="doc-actions">
                    <button class="btn-action btn-view" title="预览">
                      <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn-action btn-download" title="下载">
                      <i class="fas fa-download"></i>
                    </button>
                    <button class="btn-action btn-delete" title="删除">
                      <i class="fas fa-trash"></i>
                    </button>
                  </div>
                </div>

                <div class="document-item">
                  <div class="doc-icon">
                    <i class="fas fa-file-excel"></i>
                  </div>
                  <div class="doc-info">
                    <h4>碳排放计算表.xlsx</h4>
                    <p class="doc-meta">
                      <span><i class="fas fa-calendar"></i> 2024-01-05</span>
                      <span><i class="fas fa-weight"></i> 2.8MB</span>
                      <span><i class="fas fa-hashtag"></i> 计算、环保</span>
                    </p>
                    <p class="doc-status">
                      <i class="fas fa-sync-alt status-warning"></i> 处理中
                    </p>
                  </div>
                  <div class="doc-actions">
                    <button class="btn-action btn-view" title="预览">
                      <i class="fas fa-eye"></i>
                    </button>
                    <button class="btn-action btn-download" title="下载">
                      <i class="fas fa-download"></i>
                    </button>
                    <button class="btn-action btn-delete" title="删除">
                      <i class="fas fa-trash"></i>
                    </button>
                  </div>
                </div>
              </div>

              <!-- 知识库设置 -->
              <div class="knowledge-settings">
                <h3>知识库设置</h3>
                <div class="settings-grid">
                  <div class="setting-item">
                    <label>向量模型</label>
                    <select v-model="knowledgeSettings.vectorModel">
                      <option value="text-embedding-3-small">text-embedding-3-small</option>
                      <option value="text-embedding-3-large">text-embedding-3-large</option>
                      <option value="bge-large-zh">BGE-large-zh</option>
                    </select>
                  </div>
                  <div class="setting-item">
                    <label>相似度阈值</label>
                    <input type="range" v-model="knowledgeSettings.similarityThreshold" min="0.1" max="1" step="0.1">
                    <span>{{ knowledgeSettings.similarityThreshold }}</span>
                  </div>
                  <div class="setting-item">
                    <label>分块大小</label>
                    <input type="number" v-model="knowledgeSettings.chunkSize" min="100" max="2000">
                    <span>字符</span>
                  </div>
                  <div class="setting-item">
                    <label>分块重叠</label>
                    <input type="number" v-model="knowledgeSettings.chunkOverlap" min="0" max="500">
                    <span>字符</span>
                  </div>
                </div>
                <div class="settings-actions">
                  <button class="btn-save" @click="saveKnowledgeSettings">
                    <i class="fas fa-save"></i> 保存设置
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 编辑用户对话框 -->
    <div v-if="showEditDialog" class="modal-overlay" @click.self="closeEditDialog">
      <div class="modal-dialog">
        <div class="modal-header">
          <h3>编辑用户</h3>
          <button class="modal-close" @click="closeEditDialog">
            <i class="fas fa-times"></i>
          </button>
        </div>

        <div class="modal-content">
          <form @submit.prevent="saveUser">
            <div class="form-group">
              <label for="edit-username">用户名</label>
              <input type="text" id="edit-username" v-model="editForm.username" required>
            </div>

            <div class="form-group">
              <label for="edit-email">邮箱</label>
              <input type="email" id="edit-email" v-model="editForm.email" required>
            </div>

            <div class="form-group">
              <label for="edit-realName">真实姓名</label>
              <input type="text" id="edit-realName" v-model="editForm.realName">
            </div>

            <div class="form-group">
              <label for="edit-organization">单位/组织</label>
              <input type="text" id="edit-organization" v-model="editForm.organization">
            </div>

            <div class="form-group">
              <label for="edit-role">角色</label>
              <select id="edit-role" v-model="editForm.role">
                <option value="user">普通用户</option>
                <option value="admin">管理员</option>
              </select>
            </div>

            <div class="form-group">
              <label for="edit-status">账户状态</label>
              <select id="edit-status" v-model="editForm.accountStatus">
                <option value="active">活跃</option>
                <option value="inactive">禁用</option>
              </select>
            </div>
          </form>
        </div>

        <div class="modal-footer">
          <button class="btn-cancel" @click="closeEditDialog">取消</button>
          <button class="btn-save" @click="saveUser" :disabled="isSavingUser">
            <i v-if="isSavingUser" class="fas fa-spinner fa-spin"></i>
            {{ isSavingUser ? '保存中...' : '保存' }}
          </button>
        </div>
      </div>
    </div>

    <!-- 删除确认对话框 -->
    <div v-if="showDeleteConfirm" class="modal-overlay" @click.self="cancelDelete">
      <div class="modal-dialog delete-dialog">
        <div class="modal-header">
          <h3><i class="fas fa-exclamation-triangle"></i> 确认删除</h3>
        </div>

        <div class="modal-content">
          <p v-if="deleteType === 'single'">
            确定要删除用户 <strong>{{ userToDelete.username }}</strong> 吗？此操作不可恢复。
          </p>
          <p v-else>
            确定要删除选中的 <strong>{{ selectedUsers.length }}</strong> 个用户吗？此操作不可恢复。
          </p>
          <p class="warning-text">
            <i class="fas fa-info-circle"></i> 注意：删除用户将永久移除所有相关数据。
          </p>
        </div>

        <div class="modal-footer">
          <button class="btn-cancel" @click="cancelDelete">取消</button>
          <button class="btn-delete" @click="deleteType === 'single' ? deleteUser() : deleteUsersBatch()">
            <i class="fas fa-trash"></i> 确认删除
          </button>
        </div>
      </div>
    </div>

    <!-- 消息提示 -->
    <div v-if="message.show" :class="['message-toast', message.type]" @click="hideMessage">
      <i :class="message.icon"></i>
      <span>{{ message.text }}</span>
    </div>
  </div>
</template>

<script>
import request from '@/utils/request';
import { getCurrentUser, isLoggedIn, isAdmin, getDisplayName, getUserRole } from '@/utils/auth.js';

export default {
  name: 'MyProfile',

  data() {
    return {
      // 用户信息
      currentUser: null,
      displayName: '',
      userRole: '',
      isAdmin: false,
      currentUserId: null,

      // 页面状态
      loading: false,
      activeTab: 'profile',
      showMobileMenu: false,

      // 我的资料表单
      userForm: {
        username: '',
        email: '',
        realName: '',
        organization: ''
      },
      originalUserData: null,
      isSubmitting: false,

      // 安全设置表单
      passwordForm: {
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      },
      showCurrentPassword: false,
      showNewPassword: false,
      showConfirmPassword: false,
      isChangingPassword: false,

      // 用户管理
      users: [],
      loadingUsers: false,
      searchQuery: '',
      debounceTimer: null,

      // 分页
      currentPage: 1,
      pageSize: 10,
      totalItems: 0,
      totalPages: 0,

      // 选择和批量操作
      selectedUsers: [],
      selectAll: false,

      // 对话框
      showEditDialog: false,
      showDeleteConfirm: false,
      deleteType: 'single', // 'single' or 'batch'
      userToDelete: null,

      // 编辑表单
      editForm: {
        id: null,
        username: '',
        email: '',
        realName: '',
        organization: '',
        role: 'user',
        accountStatus: 'active'
      },
      isSavingUser: false,

      // ============ 新增：模型管理 ============
      newAgent: {
        name: '',
        description: '',
        model: 'qwen',
        tags: ['冶金']
      },

      // ============ 新增：知识库设置 ============
      knowledgeSettings: {
        vectorModel: 'text-embedding-3-small',
        similarityThreshold: 0.7,
        chunkSize: 1000,
        chunkOverlap: 200
      },

      // 消息提示
      message: {
        show: false,
        type: 'success', // 'success' or 'error'
        text: '',
        icon: 'fas fa-check-circle'
      },
      messageTimer: null
    };
  },

  computed: {
    // 我的资料表单是否有修改
    isProfileFormChanged() {
      if (!this.originalUserData) return false;
      return JSON.stringify(this.userForm) !== JSON.stringify(this.originalUserData);
    },

    // 密码表单是否有效
    isPasswordFormValid() {
      return (
          this.passwordForm.currentPassword &&
          this.passwordForm.newPassword &&
          this.passwordForm.confirmPassword &&
          this.passwordsMatch &&
          this.passwordStrength !== 'weak'
      );
    },

    // 密码是否匹配
    passwordsMatch() {
      return this.passwordForm.newPassword === this.passwordForm.confirmPassword;
    },

    // 密码强度
    passwordStrength() {
      const password = this.passwordForm.newPassword;
      if (!password) return 'empty';

      let strength = 0;
      if (password.length >= 8) strength++;
      if (/[a-z]/.test(password)) strength++;
      if (/[A-Z]/.test(password)) strength++;
      if (/[0-9]/.test(password)) strength++;
      if (/[^a-zA-Z0-9]/.test(password)) strength++;

      if (strength <= 2) return 'weak';
      if (strength <= 4) return 'medium';
      return 'strong';
    },

    passwordStrengthText() {
      const map = {
        empty: '未输入',
        weak: '弱',
        medium: '中',
        strong: '强'
      };
      return map[this.passwordStrength];
    },

    // 用户管理分页相关
    totalUsers() {
      return this.totalItems;
    },

    startItem() {
      return (this.currentPage - 1) * this.pageSize + 1;
    },

    endItem() {
      const end = this.currentPage * this.pageSize;
      return end > this.totalItems ? this.totalItems : end;
    },

    pageNumbers() {
      const pages = [];
      const maxPages = 5;

      if (this.totalPages <= maxPages) {
        for (let i = 1; i <= this.totalPages; i++) {
          pages.push(i);
        }
      } else {
        if (this.currentPage <= 3) {
          for (let i = 1; i <= 4; i++) pages.push(i);
          pages.push('...');
          pages.push(this.totalPages);
        } else if (this.currentPage >= this.totalPages - 2) {
          pages.push(1);
          pages.push('...');
          for (let i = this.totalPages - 3; i <= this.totalPages; i++) pages.push(i);
        } else {
          pages.push(1);
          pages.push('...');
          pages.push(this.currentPage - 1);
          pages.push(this.currentPage);
          pages.push(this.currentPage + 1);
          pages.push('...');
          pages.push(this.totalPages);
        }
      }

      return pages;
    }
  },

  created() {
    this.initUserData();
    this.loadCurrentUserProfile();
  },

  watch: {
    activeTab(newTab) {
      if (newTab === 'users' && this.isAdmin) {
        this.loadUsers();
      }
      this.showMobileMenu = false;
    },

    searchQuery() {
      this.currentPage = 1;
    }
  },

  methods: {
    // 初始化用户数据
    initUserData() {
      this.currentUser = getCurrentUser();
      if (this.currentUser) {
        this.displayName = getDisplayName();
        this.userRole = getUserRole();
        this.isAdmin = isAdmin();
        this.currentUserId = this.currentUser.id;
      } else {
        this.$router.push('/login');
      }
    },

    // 切换标签页
    switchTab(tab) {
      this.activeTab = tab;
    },

    // 切换移动端菜单
    toggleMobileMenu() {
      this.showMobileMenu = !this.showMobileMenu;
    },

    // 加载当前用户资料
    async loadCurrentUserProfile() {
      this.loading = true;
      try {
        const response = await request.get('/user/profile');
        if (response.code === 200) {
          const userData = response.data;
          this.userForm = {
            username: userData.username,
            email: userData.email,
            realName: userData.realName || '',
            organization: userData.organization || ''
          };
          this.originalUserData = { ...this.userForm };
        }
      } catch (error) {
        this.showMessage('error', error.message || '加载用户资料失败');
      } finally {
        this.loading = false;
      }
    },

    // 更新个人资料
    async updateProfile() {
      if (!this.isProfileFormChanged) return;

      this.isSubmitting = true;
      try {
        const response = await request.put('/user/profile', this.userForm);
        if (response.code === 200) {
          this.originalUserData = { ...this.userForm };

          // 更新本地存储的用户信息
          const storedUser = getCurrentUser();
          if (storedUser) {
            storedUser.username = this.userForm.username;
            storedUser.email = this.userForm.email;
            storedUser.realName = this.userForm.realName;
            localStorage.setItem('user', JSON.stringify(storedUser));

            // 触发Header更新
            window.dispatchEvent(new Event('storage'));
          }

          this.showMessage('success', '个人资料更新成功');
        }
      } catch (error) {
        this.showMessage('error', error.message || '更新失败');
      } finally {
        this.isSubmitting = false;
      }
    },

    // 重置个人资料表单
    resetProfileForm() {
      this.userForm = { ...this.originalUserData };
    },

    // 修改密码
    async changePassword() {
      if (!this.isPasswordFormValid) return;

      this.isChangingPassword = true;
      try {
        const response = await request.put('/user/password', {
          currentPassword: this.passwordForm.currentPassword,
          newPassword: this.passwordForm.newPassword
        });

        if (response.code === 200) {
          this.showMessage('success', '密码修改成功');
          this.resetPasswordForm();
        }
      } catch (error) {
        this.showMessage('error', error.message || '密码修改失败');
      } finally {
        this.isChangingPassword = false;
      }
    },

    // 重置密码表单
    resetPasswordForm() {
      this.passwordForm = {
        currentPassword: '',
        newPassword: '',
        confirmPassword: ''
      };
      this.showCurrentPassword = false;
      this.showNewPassword = false;
      this.showConfirmPassword = false;
    },

    // 加载用户列表
    async loadUsers() {
      this.loadingUsers = true;
      try {
        const params = {
          page: this.currentPage,
          limit: this.pageSize,
          search: this.searchQuery || undefined
        };

        const response = await request.get('/admin/users', { params });
        if (response.code === 200) {
          this.users = response.data.users;
          this.totalItems = response.data.total;
          this.totalPages = Math.ceil(this.totalItems / this.pageSize);
          this.selectedUsers = [];
          this.selectAll = false;
        }
      } catch (error) {
        this.showMessage('error', error.message || '加载用户列表失败');
      } finally {
        this.loadingUsers = false;
      }
    },

    // 防抖搜索
    debouncedSearch() {
      clearTimeout(this.debounceTimer);
      this.debounceTimer = setTimeout(() => {
        this.loadUsers();
      }, 500);
    },

    // 切换全选
    toggleSelectAll() {
      if (this.selectAll) {
        this.selectedUsers = this.users
            .filter(user => user.id !== this.currentUserId)
            .map(user => user.id);
      } else {
        this.selectedUsers = [];
      }
    },

    // 切换页码
    changePage(page) {
      if (page < 1 || page > this.totalPages || page === this.currentPage) return;
      this.currentPage = page;
      this.loadUsers();
    },

    // 编辑用户
    editUser(user) {
      this.editForm = {
        id: user.id,
        username: user.username,
        email: user.email,
        realName: user.real_name || '',
        organization: user.organization || '',
        role: user.role || 'user',
        accountStatus: user.account_status || 'active'
      };
      this.showEditDialog = true;
    },

    // 关闭编辑对话框
    closeEditDialog() {
      this.showEditDialog = false;
      this.editForm = {
        id: null,
        username: '',
        email: '',
        realName: '',
        organization: '',
        role: 'user',
        accountStatus: 'active'
      };
      this.isSavingUser = false;
    },

    // 保存用户编辑
    async saveUser() {
      if (!this.editForm.username || !this.editForm.email) {
        this.showMessage('error', '用户名和邮箱为必填项');
        return;
      }

      this.isSavingUser = true;
      try {
        const response = await request.put(`/admin/users/${this.editForm.id}`, this.editForm);
        if (response.code === 200) {
          this.showMessage('success', '用户信息更新成功');
          this.closeEditDialog();
          this.loadUsers();

          // 如果编辑的是当前用户，更新本地存储
          if (this.editForm.id === this.currentUserId) {
            const storedUser = getCurrentUser();
            if (storedUser) {
              storedUser.username = this.editForm.username;
              storedUser.email = this.editForm.email;
              storedUser.realName = this.editForm.realName;
              storedUser.role = this.editForm.role;
              localStorage.setItem('user', JSON.stringify(storedUser));
              window.dispatchEvent(new Event('storage'));
            }
          }
        }
      } catch (error) {
        this.showMessage('error', error.message || '保存失败');
      } finally {
        this.isSavingUser = false;
      }
    },

    // 确认删除单个用户
    confirmDeleteUser(user) {
      this.userToDelete = user;
      this.deleteType = 'single';
      this.showDeleteConfirm = true;
    },

    // 确认批量删除
    confirmBatchDelete() {
      this.deleteType = 'batch';
      this.showDeleteConfirm = true;
    },

    // 取消删除
    cancelDelete() {
      this.showDeleteConfirm = false;
      this.userToDelete = null;
    },

    // 删除单个用户
    async deleteUser() {
      try {
        const response = await request.delete(`/admin/users/${this.userToDelete.id}`);
        if (response.code === 200) {
          this.showMessage('success', '用户删除成功');
          this.cancelDelete();
          this.loadUsers();
        }
      } catch (error) {
        this.showMessage('error', error.message || '删除失败');
        this.cancelDelete();
      }
    },

    // 批量删除用户
    async deleteUsersBatch() {
      try {
        const response = await request.delete('/admin/users/batch', {
          data: { userIds: this.selectedUsers }
        });

        if (response.code === 200) {
          this.showMessage('success', `成功删除 ${response.data.deletedCount} 个用户`);
          this.cancelDelete();
          this.loadUsers();
        }
      } catch (error) {
        this.showMessage('error', error.message || '批量删除失败');
        this.cancelDelete();
      }
    },

    // ============ 新增：模型管理方法 ============
    editModel(modelId) {
      this.showMessage('info', `正在配置模型: ${modelId}`);
      // 这里可以打开模型配置对话框
    },

    testModel(modelId) {
      this.showMessage('info', `正在测试模型: ${modelId}`);
      // 这里可以调用模型测试接口
    },

    showAddModal(type) {
      this.showMessage('info', `添加${type === 'api' ? 'API' : '本地'}模型`);
    },

    // ============ 新增：智能体管理方法 ============
    editAgent(agentId) {
      this.showMessage('info', `编辑智能体: ${agentId}`);
    },

    configureAgent(agentId) {
      this.showMessage('info', `配置智能体: ${agentId}`);
    },

    testAgent(agentId) {
      this.showMessage('info', `测试智能体: ${agentId}`);
    },

    toggleTag(tag) {
      const index = this.newAgent.tags.indexOf(tag);
      if (index === -1) {
        this.newAgent.tags.push(tag);
      } else {
        this.newAgent.tags.splice(index, 1);
      }
    },

    resetNewAgent() {
      this.newAgent = {
        name: '',
        description: '',
        model: 'qwen',
        tags: ['冶金']
      };
    },

    async createAgent() {
      if (!this.newAgent.name.trim()) {
        this.showMessage('error', '请输入智能体名称');
        return;
      }

      this.showMessage('success', `创建智能体: ${this.newAgent.name}`);
      // 这里可以调用后端API创建智能体
    },

    // ============ 新增：知识库管理方法 ============
    showUploadModal() {
      this.showMessage('info', '打开文档上传窗口');
      // 这里可以打开文件上传对话框
    },

    async syncKnowledgeBase() {
      this.showMessage('info', '正在同步向量库...');
      // 这里可以调用向量库同步接口
    },

    async saveKnowledgeSettings() {
      this.showMessage('success', '知识库设置已保存');
      // 这里可以调用后端API保存设置
    },

    // 格式化日期
    formatDate(dateString) {
      if (!dateString) return '';
      const date = new Date(dateString);
      return date.toLocaleDateString('zh-CN') + ' ' + date.toLocaleTimeString('zh-CN', {
        hour: '2-digit',
        minute: '2-digit'
      });
    },

    // 显示消息提示
    showMessage(type, text) {
      clearTimeout(this.messageTimer);

      this.message = {
        show: true,
        type: type,
        text: text,
        icon: type === 'success' ? 'fas fa-check-circle' :
            type === 'error' ? 'fas fa-exclamation-circle' :
                type === 'info' ? 'fas fa-info-circle' : 'fas fa-check-circle'
      };

      this.messageTimer = setTimeout(() => {
        this.hideMessage();
      }, 3000);
    },

    // 隐藏消息提示
    hideMessage() {
      this.message.show = false;
      clearTimeout(this.messageTimer);
    }
  }
};
</script>

<style scoped>
/* 主容器 */
.profile-container {
  min-height: calc(100vh - 90px);
  background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
  padding-top: 90px;
  padding-bottom: 40px;
}

/* 页面头部 */
.profile-header {
  padding: 30px 40px 20px;
  border-bottom: 1px solid rgba(0, 70, 219, 0.1);
  background: white;
  box-shadow: 0 2px 10px rgba(0, 70, 219, 0.05);
}

.profile-header h1 {
  font-size: 28px;
  color: #0046DB;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 12px;
}

.profile-header h1 i {
  font-size: 32px;
}

.user-welcome {
  font-size: 16px;
  color: #666;
  display: flex;
  align-items: center;
  gap: 15px;
}

.user-name {
  color: #0046DB;
  font-weight: 600;
}

.user-role-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.user-role-badge.admin {
  background: linear-gradient(135deg, #ff6b6b, #ee5a52);
  color: white;
}

.user-role-badge.user {
  background: linear-gradient(135deg, #4ecdc4, #44a08d);
  color: white;
}

/* 加载状态 */
.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 100px 20px;
}

.loading-spinner {
  width: 50px;
  height: 50px;
  border: 3px solid rgba(0, 70, 219, 0.1);
  border-radius: 50%;
  border-top-color: #0046DB;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

/* 主要内容区域 */
.profile-content {
  display: flex;
  max-width: 1400px;
  margin: 0 auto;
  padding: 30px 20px;
  gap: 30px;
}

/* 左侧导航 */
.profile-sidebar {
  width: 280px; /* 增加宽度以适应新菜单 */
  flex-shrink: 0;
}

.sidebar-nav {
  background: white;
  border-radius: 12px;
  padding: 20px 0;
  box-shadow: 0 5px 20px rgba(0, 70, 219, 0.08);
}

.nav-item {
  display: flex;
  align-items: center;
  padding: 15px 25px;
  color: #666;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.3s ease;
  border-left: 4px solid transparent;
  position: relative;
}

.nav-item:hover {
  color: #0046DB;
  background: rgba(0, 70, 219, 0.05);
}

.nav-item.active {
  color: #0046DB;
  background: rgba(0, 70, 219, 0.1);
  border-left-color: #0046DB;
  font-weight: 600;
}

.nav-item i {
  width: 20px;
  margin-right: 12px;
  font-size: 16px;
}

/* 管理员专属区域 */
.admin-section {
  margin-top: 20px;
  border-top: 1px solid #eee;
  padding-top: 20px;
}

.section-title {
  padding: 0 25px 15px;
  color: #666;
  font-size: 12px;
  text-transform: uppercase;
  letter-spacing: 1px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-title i {
  color: #ffc107;
  font-size: 14px;
}

.user-count {
  position: absolute;
  right: 25px;
  background: #ff6b6b;
  color: white;
  font-size: 12px;
  padding: 2px 8px;
  border-radius: 10px;
  font-weight: 600;
}

.feature-badge {
  position: absolute;
  right: 25px;
  background: linear-gradient(135deg, #40c057, #2f9e44);
  color: white;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 8px;
  font-weight: 600;
}

/* 移动端菜单按钮 */
.mobile-menu-btn {
  display: none;
  position: fixed;
  bottom: 30px;
  right: 30px;
  width: 50px;
  height: 50px;
  background: #0046DB;
  color: white;
  border: none;
  border-radius: 50%;
  font-size: 20px;
  z-index: 1000;
  box-shadow: 0 4px 15px rgba(0, 70, 219, 0.3);
  cursor: pointer;
}

/* 右侧主内容 */
.profile-main {
  flex: 1;
  min-width: 0;
}

/* 标签页内容 */
.tab-content {
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 5px 20px rgba(0, 70, 219, 0.08);
  min-height: 500px;
}

.section-header {
  margin-bottom: 30px;
  padding-bottom: 20px;
  border-bottom: 1px solid #eee;
}

.section-header h2 {
  font-size: 24px;
  color: #333;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.section-header h2 i {
  color: #0046DB;
}

.section-subtitle {
  color: #666;
  font-size: 14px;
}

/* ============ 新增：AI管理样式 ============ */
.ai-management-container {
  padding: 20px 0;
}

/* 统计概览 */
.stats-overview {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.stat-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 25px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  gap: 20px;
  transition: transform 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-5px);
}

.stat-card:nth-child(2) {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-card:nth-child(3) {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-icon {
  font-size: 32px;
  opacity: 0.8;
}

.stat-content h3 {
  font-size: 14px;
  font-weight: 600;
  margin-bottom: 8px;
  opacity: 0.9;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 5px;
}

.stat-desc {
  font-size: 12px;
  opacity: 0.8;
}

/* 模型管理 */
.model-config-section {
  margin-top: 30px;
}

.model-config-section h3 {
  font-size: 20px;
  color: #333;
  margin-bottom: 20px;
  padding-bottom: 10px;
  border-bottom: 1px solid #eee;
}

.model-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.model-card {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 20px;
  border: 1px solid #e1e5eb;
  transition: all 0.3s ease;
}

.model-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 10px 25px rgba(0, 0, 0, 0.1);
}

.model-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 15px;
}

.model-info {
  display: flex;
  gap: 15px;
  align-items: flex-start;
}

.model-info i {
  font-size: 28px;
  color: #0046DB;
  margin-top: 5px;
}

.model-info h4 {
  font-size: 18px;
  color: #333;
  margin-bottom: 8px;
}

.model-tag {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 15px;
  font-size: 12px;
  font-weight: 600;
  margin-right: 8px;
  margin-bottom: 5px;
}

.model-tag.active {
  background: rgba(40, 167, 69, 0.1);
  color: #28a745;
}

.model-tag.warning {
  background: rgba(255, 193, 7, 0.1);
  color: #ffc107;
}

.model-tag.api-key {
  background: rgba(0, 123, 255, 0.1);
  color: #007bff;
}

.model-tag.local {
  background: rgba(111, 66, 193, 0.1);
  color: #6f42c1;
}

.model-details {
  margin-top: 15px;
}

.model-details p {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 10px;
}

.model-details i {
  color: #0046DB;
  width: 16px;
}

.status-success {
  color: #28a745;
  font-weight: 600;
}

.status-warning {
  color: #ffc107;
  font-weight: 600;
}

.model-actions {
  display: flex;
  gap: 10px;
}

.btn-action {
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 5px;
}

.btn-edit {
  background: linear-gradient(135deg, #4ecdc4, #44a08d);
  color: white;
}

.btn-test {
  background: linear-gradient(135deg, #ffd166, #ffb347);
  color: white;
}

.btn-config {
  background: linear-gradient(135deg, #118ab2, #06d6a0);
  color: white;
}

.btn-action:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

/* 添加模型区域 */
.add-model-section {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  padding: 30px;
  border-radius: 12px;
  margin-top: 30px;
}

.add-model-section h4 {
  font-size: 20px;
  margin-bottom: 20px;
  text-align: center;
}

.add-model-options {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
}

.add-option {
  background: rgba(255, 255, 255, 0.1);
  border: 2px dashed rgba(255, 255, 255, 0.3);
  border-radius: 10px;
  padding: 25px 20px;
  color: white;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.add-option:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: translateY(-3px);
}

.add-option i {
  font-size: 32px;
  opacity: 0.9;
}

.add-option span {
  font-size: 16px;
  font-weight: 600;
}

.add-option small {
  font-size: 12px;
  opacity: 0.8;
  text-align: center;
}

/* 智能体管理 */
.agents-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
  gap: 25px;
  margin-bottom: 30px;
}

.agent-card {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 25px;
  border: 1px solid #e1e5eb;
  transition: all 0.3s ease;
}

.agent-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 15px 30px rgba(0, 0, 0, 0.1);
}

.agent-header {
  display: flex;
  gap: 20px;
  margin-bottom: 20px;
}

.agent-avatar {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, #0046DB, #0033a0);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: white;
  flex-shrink: 0;
}

.agent-info {
  flex: 1;
}

.agent-info h3 {
  font-size: 20px;
  color: #333;
  margin-bottom: 8px;
}

.agent-desc {
  font-size: 14px;
  color: #666;
  margin-bottom: 12px;
}

.agent-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tag {
  padding: 4px 12px;
  background: rgba(0, 70, 219, 0.1);
  color: #0046DB;
  border-radius: 15px;
  font-size: 12px;
  font-weight: 600;
}

.agent-status {
  text-align: right;
}

.agent-status .stat {
  font-size: 12px;
  color: #666;
  margin-top: 8px;
}

.agent-actions {
  display: flex;
  gap: 10px;
  justify-content: flex-end;
  border-top: 1px solid #e1e5eb;
  padding-top: 20px;
}

/* 创建智能体 */
.create-agent-section {
  background: white;
  border-radius: 12px;
  padding: 25px;
  border: 2px solid #e1e5eb;
  margin-top: 30px;
}

.create-agent-section h3 {
  font-size: 20px;
  color: #333;
  margin-bottom: 20px;
}

.create-form {
  display: grid;
  gap: 20px;
}

.tag-selection {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.tag-selectable {
  padding: 8px 16px;
  background: #f8f9fa;
  border: 2px solid #e1e5eb;
  border-radius: 20px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.tag-selectable:hover {
  border-color: #0046DB;
}

.tag-selectable.selected {
  background: #0046DB;
  color: white;
  border-color: #0046DB;
}

/* 知识库管理 */
.knowledge-management {
  margin-top: 30px;
}

.knowledge-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
  padding-bottom: 15px;
  border-bottom: 1px solid #eee;
}

.knowledge-header h3 {
  font-size: 20px;
  color: #333;
}

.knowledge-actions {
  display: flex;
  gap: 15px;
}

.btn-upload {
  background: linear-gradient(135deg, #40c057, #2f9e44);
  color: white;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-sync {
  background: linear-gradient(135deg, #17a2b8, #138496);
  color: white;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 文档列表 */
.documents-list {
  margin-bottom: 30px;
}

.document-item {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 10px;
  margin-bottom: 15px;
  border: 1px solid #e1e5eb;
  transition: all 0.3s ease;
}

.document-item:hover {
  background: #fff;
  transform: translateX(5px);
}

.doc-icon {
  font-size: 32px;
  color: #0046DB;
}

.doc-info {
  flex: 1;
}

.doc-info h4 {
  font-size: 16px;
  color: #333;
  margin-bottom: 8px;
}

.doc-meta {
  display: flex;
  gap: 20px;
  font-size: 12px;
  color: #666;
  margin-bottom: 8px;
}

.doc-meta span {
  display: flex;
  align-items: center;
  gap: 5px;
}

.doc-status {
  font-size: 12px;
  color: #666;
  display: flex;
  align-items: center;
  gap: 8px;
}

.doc-actions {
  display: flex;
  gap: 10px;
}

.btn-view {
  background: #4ecdc4;
  color: white;
}

.btn-download {
  background: #17a2b8;
  color: white;
}

.btn-delete {
  background: #ff6b6b;
  color: white;
}

/* 知识库设置 */
.knowledge-settings {
  background: #f8f9fa;
  border-radius: 12px;
  padding: 25px;
  border: 1px solid #e1e5eb;
}

.knowledge-settings h3 {
  font-size: 18px;
  color: #333;
  margin-bottom: 20px;
}

.settings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 25px;
}

.setting-item {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.setting-item label {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

.setting-item select,
.setting-item input[type="number"] {
  padding: 10px 15px;
  border: 2px solid #e1e5eb;
  border-radius: 6px;
  font-size: 14px;
}

.setting-item input[type="range"] {
  width: 100%;
}

.settings-actions {
  text-align: right;
}

/* ============ 原有样式保持不变 ============ */
/* ... 原有的表单样式、表格样式、模态框样式等保持不变 ... */

/* 用户管理头部操作 */
.header-actions {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 20px;
}

.search-box {
  position: relative;
  width: 300px;
}

.search-box i {
  position: absolute;
  left: 15px;
  top: 50%;
  transform: translateY(-50%);
  color: #999;
}

.search-box input {
  width: 100%;
  padding: 12px 15px 12px 45px;
  border: 2px solid #e1e5eb;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s ease;
}

.search-box input:focus {
  outline: none;
  border-color: #0046DB;
  box-shadow: 0 0 0 3px rgba(0, 70, 219, 0.1);
}

.btn-delete-batch {
  background: linear-gradient(135deg, #ff6b6b, #ee5a52);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-delete-batch:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(255, 107, 107, 0.3);
}

.btn-delete-batch:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

/* 表单样式 */
.form-group {
  margin-bottom: 25px;
  position: relative;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #333;
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-group label i {
  color: #0046DB;
  font-size: 14px;
}

.form-group input,
.form-group select,
.form-group textarea {
  width: 100%;
  padding: 12px 15px;
  border: 2px solid #e1e5eb;
  border-radius: 8px;
  font-size: 14px;
  transition: all 0.3s ease;
}

.form-group input:focus,
.form-group select:focus,
.form-group textarea:focus {
  outline: none;
  border-color: #0046DB;
  box-shadow: 0 0 0 3px rgba(0, 70, 219, 0.1);
}

.form-group input:disabled,
.form-group select:disabled {
  background-color: #f8f9fa;
  cursor: not-allowed;
}

.form-hint {
  font-size: 12px;
  color: #666;
  margin-top: 5px;
}

.form-hint.error {
  color: #ff6b6b;
}

/* 密码强度指示器 */
.password-strength {
  margin-top: 8px;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 600;
  text-align: center;
}

.password-strength.weak {
  background: rgba(255, 107, 107, 0.1);
  color: #ff6b6b;
}

.password-strength.medium {
  background: rgba(255, 193, 7, 0.1);
  color: #ffc107;
}

.password-strength.strong {
  background: rgba(40, 167, 69, 0.1);
  color: #28a745;
}

/* 密码显示切换按钮 */
.password-toggle {
  position: absolute;
  right: 15px;
  top: 40px;
  color: #999;
  cursor: pointer;
  transition: color 0.3s ease;
}

.password-toggle:hover {
  color: #0046DB;
}

/* 表单操作按钮 */
.form-actions {
  display: flex;
  justify-content: flex-end;
  gap: 15px;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #eee;
}

.btn-cancel,
.btn-save {
  padding: 12px 30px;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-cancel {
  background: #f8f9fa;
  color: #666;
}

.btn-cancel:hover:not(:disabled) {
  background: #e9ecef;
}

.btn-save {
  background: linear-gradient(135deg, #0046DB, #0033a0);
  color: white;
}

.btn-save:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 70, 219, 0.3);
}

.btn-cancel:disabled,
.btn-save:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: none !important;
}

/* 用户表格 */
.users-table-container {
  margin-top: 20px;
}

.table-responsive {
  overflow-x: auto;
  border-radius: 8px;
  border: 1px solid #e1e5eb;
}

.users-table {
  width: 100%;
  border-collapse: collapse;
  min-width: 1200px;
}

.users-table th {
  background: linear-gradient(135deg, #f8f9fa, #e9ecef);
  padding: 15px;
  text-align: left;
  font-weight: 600;
  color: #333;
  border-bottom: 2px solid #dee2e6;
}

.users-table td {
  padding: 15px;
  border-bottom: 1px solid #e1e5eb;
  vertical-align: middle;
}

.users-table tr:last-child td {
  border-bottom: none;
}

.users-table tr:hover td {
  background-color: rgba(0, 70, 219, 0.02);
}

.users-table tr.current-user td {
  background-color: rgba(0, 70, 219, 0.05);
}

/* 表格加载和空状态 */
.loading-row,
.empty-row {
  text-align: center;
  padding: 60px !important;
}

.table-loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.table-loading .spinner {
  width: 30px;
  height: 30px;
  border: 3px solid rgba(0, 70, 219, 0.1);
  border-radius: 50%;
  border-top-color: #0046DB;
  animation: spin 1s linear infinite;
}

.empty-row {
  color: #666;
}

.empty-row i {
  font-size: 48px;
  margin-bottom: 15px;
  color: #ccc;
}

.empty-row p {
  font-size: 16px;
}

/* 表格中的徽章 */
.role-badge,
.status-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 12px;
  font-weight: 600;
}

.role-badge.admin {
  background: linear-gradient(135deg, #ff6b6b, #ee5a52);
  color: white;
}

.role-badge.user {
  background: linear-gradient(135deg, #4ecdc4, #44a08d);
  color: white;
}

.status-badge.active {
  background: linear-gradient(135deg, #40c057, #2f9e44);
  color: white;
}

.status-badge.inactive {
  background: linear-gradient(135deg, #868e96, #495057);
  color: white;
}

/* 表格操作按钮 */
.actions {
  display: flex;
  gap: 8px;
}

.btn-edit,
.btn-delete {
  padding: 6px 12px;
  border: none;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 5px;
}

.btn-edit {
  background: linear-gradient(135deg, #4ecdc4, #44a08d);
  color: white;
}

.btn-edit:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(78, 205, 196, 0.3);
}

.btn-delete {
  background: linear-gradient(135deg, #ff6b6b, #ee5a52);
  color: white;
}

.btn-delete:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(255, 107, 107, 0.3);
}

.btn-edit:disabled,
.btn-delete:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: none !important;
}

/* 分页 */
.pagination-container {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 20px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
}

.pagination-info {
  color: #666;
  font-size: 14px;
}

.pagination-controls {
  display: flex;
  align-items: center;
  gap: 10px;
}

.pagination-btn,
.page-btn {
  padding: 8px 15px;
  border: 1px solid #dee2e6;
  background: white;
  color: #333;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 5px;
}

.pagination-btn:hover:not(:disabled),
.page-btn:hover:not(:disabled) {
  background: #0046DB;
  color: white;
  border-color: #0046DB;
}

.pagination-btn:disabled,
.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-btn.active {
  background: #0046DB;
  color: white;
  border-color: #0046DB;
  font-weight: 600;
}

.page-numbers {
  display: flex;
  gap: 5px;
}

/* 模态对话框 */
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 20px;
}

.modal-dialog {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
  animation: modalSlideIn 0.3s ease;
}

@keyframes modalSlideIn {
  from {
    opacity: 0;
    transform: translateY(-30px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.modal-header {
  padding: 20px 25px;
  border-bottom: 1px solid #e1e5eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h3 {
  font-size: 20px;
  color: #333;
  display: flex;
  align-items: center;
  gap: 10px;
}

.modal-close {
  background: none;
  border: none;
  font-size: 20px;
  color: #666;
  cursor: pointer;
  padding: 5px;
  border-radius: 4px;
}

.modal-close:hover {
  background: #f8f9fa;
  color: #333;
}

.modal-content {
  padding: 25px;
}

.modal-footer {
  padding: 20px 25px;
  border-top: 1px solid #e1e5eb;
  display: flex;
  justify-content: flex-end;
  gap: 15px;
}

.delete-dialog .modal-content {
  text-align: center;
}

.delete-dialog .warning-text {
  color: #ff6b6b;
  background: rgba(255, 107, 107, 0.1);
  padding: 10px;
  border-radius: 6px;
  margin-top: 15px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 14px;
}

/* 消息提示 */
.message-toast {
  position: fixed;
  bottom: 30px;
  right: 30px;
  padding: 15px 25px;
  border-radius: 8px;
  color: white;
  font-weight: 600;
  display: flex;
  align-items: center;
  gap: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
  z-index: 3000;
  cursor: pointer;
  animation: toastSlideIn 0.3s ease;
  max-width: 400px;
}

@keyframes toastSlideIn {
  from {
    opacity: 0;
    transform: translateX(100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

.message-toast.success {
  background: linear-gradient(135deg, #40c057, #2f9e44);
}

.message-toast.error {
  background: linear-gradient(135deg, #ff6b6b, #ee5a52);
}

.message-toast.info {
  background: linear-gradient(135deg, #17a2b8, #138496);
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .profile-content {
    flex-direction: column;
  }

  .profile-sidebar {
    width: 100%;
    position: relative;
  }

  .sidebar-nav {
    display: none;
    position: absolute;
    top: 100%;
    left: 0;
    right: 0;
    z-index: 100;
    margin-top: 10px;
  }

  .sidebar-nav.show {
    display: block;
  }

  .mobile-menu-btn {
    display: block;
  }

  .profile-main {
    width: 100%;
  }

  .header-actions {
    flex-direction: column;
    align-items: stretch;
    gap: 15px;
  }

  .search-box {
    width: 100%;
  }

  .model-list,
  .agents-list {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .profile-header {
    padding: 20px;
  }

  .profile-header h1 {
    font-size: 24px;
  }

  .tab-content {
    padding: 20px;
  }

  .form-actions {
    flex-direction: column;
  }

  .btn-cancel,
  .btn-save {
    width: 100%;
    justify-content: center;
  }

  .users-table {
    font-size: 13px;
  }

  .users-table th,
  .users-table td {
    padding: 10px;
  }

  .actions {
    flex-direction: column;
    gap: 5px;
  }

  .pagination-container {
    flex-direction: column;
    gap: 15px;
    text-align: center;
  }

  .pagination-controls {
    flex-wrap: wrap;
    justify-content: center;
  }

  .modal-dialog {
    max-width: 95%;
  }

  .stats-overview {
    grid-template-columns: 1fr;
  }

  .settings-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .user-welcome {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }

  .section-header h2 {
    font-size: 20px;
  }

  .nav-item {
    padding: 12px 20px;
  }

  .model-header,
  .agent-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }

  .agent-status {
    text-align: left;
    width: 100%;
  }

  .knowledge-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }

  .knowledge-actions {
    width: 100%;
    flex-direction: column;
  }
}
</style>