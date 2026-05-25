<template>
  <Header></Header>
  <div class="fluid-dynamics">
    <!-- 面包屑导航 -->
    <div class="mb-nav">
      <div class="container">
        <p>
          当前位置： <router-link to="/">首页</router-link> >
          <span>冶金流体力学</span>
        </p>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="container main-content">
      <div class="data-aggregation">
        <!-- 左侧导航栏 -->
        <div class="data-aggregation-left">
          <div class="left-sub-nav-box">
            <!-- 数据库分类导航 -->
            <dl class="data-aggregation-nav"
                :class="{active: activeModule === 'overview'}"
                @click="switchModule('overview')">
              <dt class="index1">
                <a href="javascript:void(0)">流体力学概览</a>
              </dt>
            </dl>

            <!-- 流体数据库 -->
            <dl class="data-aggregation-nav"
                :class="{active: activeModule === 'database'}"
                @click="switchModule('database')">
              <dt class="index2">
                <a href="javascript:void(0)">流体力学数据库</a>
              </dt>
            </dl>

            <!-- 数值模拟 -->
            <dl class="data-aggregation-nav"
                :class="{active: activeModule === 'simulation'}"
                @click="switchModule('simulation')">
              <dt class="index3">
                <a href="javascript:void(0)">数值模拟平台</a>
              </dt>
            </dl>

            <!-- 实验数据 -->
            <dl class="data-aggregation-nav"
                :class="{active: activeModule === 'experiment'}"
                @click="switchModule('experiment')">
              <dt class="index4">
                <a href="javascript:void(0)">实验数据库</a>
              </dt>
            </dl>

            <!-- 案例分析 -->
            <dl class="data-aggregation-nav"
                :class="{active: activeModule === 'case'}"
                @click="switchModule('case')">
              <dt class="index5">
                <a href="javascript:void(0)">工业案例分析</a>
              </dt>
            </dl>

            <!-- 计算工具 -->
            <dl class="data-aggregation-nav"
                :class="{active: activeModule === 'tools'}"
                @click="switchModule('tools')">
              <dt class="index6">
                <a href="javascript:void(0)">在线计算工具</a>
              </dt>
            </dl>
          </div>
          <div class="m-nav-but">点击展开菜单</div>
        </div>

        <!-- 右侧内容展示区 -->
        <div class="data-aggregation-right">

          <!-- ==================== 概览模块 ==================== -->
          <div class="module-content" v-if="activeModule === 'overview'">
            <div class="module-header">
              <h2><i class="fas fa-tachometer-alt"></i> 冶金流体力学概览</h2>
              <p class="module-desc">冶金过程流体力学数据、模拟与分析方法，支持工艺优化与设备设计</p>
            </div>

            <!-- 关键指标 -->
            <div class="echarts-data-num">
              <div class="data-item">
                <dl>
                  <dt>流体数据记录</dt>
                  <dd>8,500+</dd>
                  <dd class="trend up">持续更新</dd>
                </dl>
                <div class="card-icon">
                  <i class="fas fa-database fa-2x"></i>
                </div>
              </div>

              <div class="data-item">
                <dl>
                  <dt>模拟案例</dt>
                  <dd>320+</dd>
                  <dd class="trend up">持续增加</dd>
                </dl>
                <div class="card-icon">
                  <i class="fas fa-chart-line fa-2x"></i>
                </div>
              </div>

              <div class="data-item">
                <dl>
                  <dt>冶金工艺</dt>
                  <dd>15+</dd>
                  <dd class="trend down">覆盖全面</dd>
                </dl>
                <div class="card-icon">
                  <i class="fas fa-industry fa-2x"></i>
                </div>
              </div>

              <div class="data-item">
                <dl>
                  <dt>在线计算工具</dt>
                  <dd>12+</dd>
                  <dd class="trend up">持续开发</dd>
                </dl>
                <div class="card-icon">
                  <i class="fas fa-calculator fa-2x"></i>
                </div>
              </div>

              <div class="data-item">
                <dl>
                  <dt>实验数据集</dt>
                  <dd>450+</dd>
                  <dd class="trend up">持续积累</dd>
                </dl>
                <div class="card-icon">
                  <i class="fas fa-flask fa-2x"></i>
                </div>
              </div>

              <div class="data-item">
                <dl>
                  <dt>工业案例</dt>
                  <dd>85+</dd>
                  <dd class="trend up">持续增加</dd>
                </dl>
                <div class="card-icon">
                  <i class="fas fa-briefcase fa-2x"></i>
                </div>
              </div>
            </div>

            <!-- 应用场景 -->
            <div class="application-scenarios mt30">
              <div class="section-header">
                <h3><i class="fas fa-cogs"></i> 主要应用场景</h3>
                <p>冶金流体力学在工业生产中的关键应用</p>
              </div>

              <div class="scenarios-grid">
                <div class="scenario-card">
                  <div class="scenario-icon">
                    <i class="fas fa-fire"></i>
                  </div>
                  <div class="scenario-content">
                    <h4>高炉煤气流动</h4>
                    <p>模拟高炉内煤气流动、分布与燃烧过程</p>
                    <div class="scenario-tags">
                      <span class="tag">气体流动</span>
                      <span class="tag">燃烧分析</span>
                    </div>
                  </div>
                </div>

                <div class="scenario-card">
                  <div class="scenario-icon">
                    <i class="fas fa-tint"></i>
                  </div>
                  <div class="scenario-content">
                    <h4>钢液流动与搅拌</h4>
                    <p>RH、LF精炼钢液流动、搅拌混合过程模拟</p>
                    <div class="scenario-tags">
                      <span class="tag">钢液流动</span>
                      <span class="tag">搅拌混合</span>
                    </div>
                  </div>
                </div>

                <div class="scenario-card">
                  <div class="scenario-icon">
                    <i class="fas fa-wind"></i>
                  </div>
                  <div class="scenario-content">
                    <h4>除尘系统优化</h4>
                    <p>除尘管道、风机系统流体动力学分析</p>
                    <div class="scenario-tags">
                      <span class="tag">气体净化</span>
                      <span class="tag">系统优化</span>
                    </div>
                  </div>
                </div>

                <div class="scenario-card">
                  <div class="scenario-icon">
                    <i class="fas fa-water"></i>
                  </div>
                  <div class="scenario-content">
                    <h4>连铸结晶器</h4>
                    <p>结晶器内钢液流动、温度分布模拟</p>
                    <div class="scenario-tags">
                      <span class="tag">凝固过程</span>
                      <span class="tag">传热传质</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- ==================== 数据库模块 ==================== -->
          <div class="module-content" v-if="activeModule === 'database'">
            <div class="module-header">
              <h2><i class="fas fa-database"></i> 流体力学数据库</h2>
              <p class="module-desc">冶金过程流体物性参数、流动特性数据与经验公式</p>
            </div>

            <!-- 数据查询 -->
            <div class="search-section">
              <div class="section-header">
                <h3><i class="fas fa-search"></i> 流体数据查询</h3>
                <p>选择查询条件，检索冶金流体力学数据</p>
              </div>

              <div class="search-form">
                <div class="form-row">
                  <div class="form-group">
                    <label for="fluid-type"><i class="fas fa-water"></i> 流体类型</label>
                    <select id="fluid-type" v-model="searchParams.fluidType">
                      <option value="">选择流体类型</option>
                      <option value="liquid-steel">钢液</option>
                      <option value="liquid-iron">铁水</option>
                      <option value="slag">熔渣</option>
                      <option value="gas-co">CO气体</option>
                      <option value="gas-n2">氮气</option>
                      <option value="gas-air">空气</option>
                    </select>
                  </div>

                  <div class="form-group">
                    <label for="property"><i class="fas fa-chart-line"></i> 物性参数</label>
                    <select id="property" v-model="searchParams.property">
                      <option value="">选择物性参数</option>
                      <option value="density">密度</option>
                      <option value="viscosity">粘度</option>
                      <option value="conductivity">导热系数</option>
                      <option value="specific-heat">比热容</option>
                      <option value="surface-tension">表面张力</option>
                    </select>
                  </div>

                  <div class="form-group">
                    <label for="temperature"><i class="fas fa-thermometer-half"></i> 温度范围 (°C)</label>
                    <div class="range-input">
                      <input type="number" v-model="searchParams.tempMin" placeholder="最小值" min="0" max="2000">
                      <span>至</span>
                      <input type="number" v-model="searchParams.tempMax" placeholder="最大值" min="0" max="2000">
                    </div>
                  </div>
                </div>

                <div class="form-actions">
                  <button class="btn-search" @click="searchFluidData">
                    <i class="fas fa-search"></i> 查询数据
                  </button>
                  <button class="btn-reset" @click="resetSearch">
                    <i class="fas fa-redo"></i> 重置条件
                  </button>
                </div>
              </div>
            </div>

            <!-- 查询结果 -->
            <div class="data-results mt30" v-if="showResults">
              <div class="results-header">
                <h3><i class="fas fa-table"></i> 流体物性查询结果</h3>
                <div class="results-info">
                  <span>共找到 {{ fluidResults.length }} 条记录</span>
                  <button class="btn-export" @click="exportData">
                    <i class="fas fa-download"></i> 导出数据
                  </button>
                </div>
              </div>

              <div class="results-table">
                <table>
                  <thead>
                  <tr>
                    <th>流体类型</th>
                    <th>温度 (°C)</th>
                    <th>密度 (kg/m³)</th>
                    <th>粘度 (Pa·s)</th>
                    <th>导热系数 (W/m·K)</th>
                    <th>比热容 (J/kg·K)</th>
                    <th>数据来源</th>
                    <th>操作</th>
                  </tr>
                  </thead>
                  <tbody>
                  <tr v-for="(item, index) in paginatedResults" :key="index">
                    <td>{{ item.type }}</td>
                    <td>{{ item.temperature }}</td>
                    <td class="value-cell">{{ item.density }}</td>
                    <td>{{ item.viscosity }}</td>
                    <td>{{ item.conductivity }}</td>
                    <td>{{ item.specificHeat }}</td>
                    <td>{{ item.source }}</td>
                    <td>
                      <button class="btn-detail" @click="viewFluidDetail(item)">
                        <i class="fas fa-info-circle"></i> 详情
                      </button>
                    </td>
                  </tr>
                  </tbody>
                </table>

                <!-- 分页 -->
                <div class="pagination" v-if="fluidResults.length > pageSize">
                  <button class="page-btn" :disabled="currentPage === 1" @click="currentPage--">
                    <i class="fas fa-chevron-left"></i> 上一页
                  </button>
                  <span class="page-info">第 {{ currentPage }} 页 / 共 {{ totalPages }} 页</span>
                  <button class="page-btn" :disabled="currentPage === totalPages" @click="currentPage++">
                    下一页 <i class="fas fa-chevron-right"></i>
                  </button>
                </div>
              </div>
            </div>

            <!-- 流体特性分类 -->
            <div class="fluid-categories mt30">
              <div class="section-header">
                <h3><i class="fas fa-layer-group"></i> 流体特性分类</h3>
                <p>不同冶金流体类型的特性参数对比</p>
              </div>

              <div class="categories-grid">
                <div class="category-card" v-for="category in fluidCategories" :key="category.id">
                  <div class="category-icon" :style="{backgroundColor: category.color}">
                    <i :class="category.icon"></i>
                  </div>
                  <div class="category-content">
                    <h4>{{ category.name }}</h4>
                    <p>{{ category.description }}</p>
                    <div class="category-stats">
                      <div class="stat">
                        <span class="stat-label">数据量</span>
                        <span class="stat-value">{{ category.dataCount }}</span>
                      </div>
                      <div class="stat">
                        <span class="stat-label">温度范围</span>
                        <span class="stat-value">{{ category.tempRange }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- ==================== 数值模拟模块 ==================== -->
          <div class="module-content" v-if="activeModule === 'simulation'">
            <div class="module-header">
              <h2><i class="fas fa-chart-area"></i> 数值模拟平台</h2>
              <p class="module-desc">冶金过程流体动力学数值模拟与可视化分析</p>
            </div>

            <!-- 模拟案例 -->
            <div class="simulation-cases">
              <div class="section-header">
                <h3><i class="fas fa-project-diagram"></i> 典型模拟案例</h3>
                <p>冶金过程流体动力学数值模拟典型案例</p>
              </div>

              <div class="cases-grid">
                <div class="case-card" v-for="caseItem in simulationCases" :key="caseItem.id">
                  <div class="case-visual">
                    <div class="mock-flow-visualization" :style="{backgroundColor: caseItem.bgColor}">
                      <div class="flow-arrow" v-for="arrow in caseItem.arrows" :key="arrow.id"
                           :style="arrow.style"></div>
                    </div>
                  </div>
                  <div class="case-content">
                    <div class="case-header">
                      <h4>{{ caseItem.title }}</h4>
                      <span class="case-tag" :style="{backgroundColor: caseItem.tagColor}">
                        {{ caseItem.type }}
                      </span>
                    </div>
                    <p>{{ caseItem.description }}</p>
                    <div class="case-meta">
                      <div class="meta-item">
                        <i class="fas fa-calculator"></i>
                        <span>网格数量：{{ caseItem.meshCount }}</span>
                      </div>
                      <div class="meta-item">
                        <i class="fas fa-clock"></i>
                        <span>计算时间：{{ caseItem.computeTime }}</span>
                      </div>
                    </div>
                    <div class="case-actions">
                      <button class="btn-detail" @click="viewSimulationDetail(caseItem)">
                        <i class="fas fa-play-circle"></i> 运行模拟
                      </button>
                      <button class="btn-case" @click="viewCaseResults(caseItem)">
                        <i class="fas fa-chart-bar"></i> 查看结果
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 模拟参数设置 -->
            <div class="simulation-params mt30">
              <div class="section-header">
                <h3><i class="fas fa-sliders-h"></i> 模拟参数设置</h3>
                <p>配置流体动力学模拟计算参数</p>
              </div>

              <div class="params-form">
                <div class="params-row">
                  <div class="param-group">
                    <label><i class="fas fa-cube"></i> 计算模型</label>
                    <select v-model="simulationParams.model">
                      <option value="rans">RANS湍流模型</option>
                      <option value="les">LES大涡模拟</option>
                      <option value="dns">DNS直接数值模拟</option>
                      <option value="vof">VOF多相流模型</option>
                    </select>
                  </div>

                  <div class="param-group">
                    <label><i class="fas fa-expand-alt"></i> 网格数量</label>
                    <input type="range" v-model="simulationParams.meshSize" min="1000" max="1000000" step="1000">
                    <span class="param-value">{{ simulationParams.meshSize.toLocaleString() }} 个</span>
                  </div>
                </div>

                <div class="params-row">
                  <div class="param-group">
                    <label><i class="fas fa-hourglass-half"></i> 时间步长 (s)</label>
                    <input type="number" v-model="simulationParams.timeStep" min="0.001" max="1" step="0.001">
                  </div>

                  <div class="param-group">
                    <label><i class="fas fa-temperature-high"></i> 温度条件</label>
                    <div class="range-input">
                      <input type="number" v-model="simulationParams.tempMin" placeholder="初始温度">
                      <span>至</span>
                      <input type="number" v-model="simulationParams.tempMax" placeholder="边界温度">
                    </div>
                  </div>
                </div>

                <div class="params-actions">
                  <button class="btn-run" @click="runSimulation">
                    <i class="fas fa-play"></i> 开始模拟计算
                  </button>
                  <button class="btn-save" @click="saveSimulationConfig">
                    <i class="fas fa-save"></i> 保存配置
                  </button>
                </div>
              </div>
            </div>
          </div>

          <!-- ==================== 实验数据库模块 ==================== -->
          <div class="module-content" v-if="activeModule === 'experiment'">
            <div class="module-header">
              <h2><i class="fas fa-flask"></i> 实验数据库</h2>
              <p class="module-desc">冶金流体力学实验数据与测量结果</p>
            </div>

            <!-- 实验设备 -->
            <div class="experiment-equipment">
              <div class="section-header">
                <h3><i class="fas fa-tools"></i> 实验设备与方法</h3>
                <p>冶金流体力学常用实验设备与测量技术</p>
              </div>

              <div class="equipment-grid">
                <div class="equipment-card" v-for="equipment in experimentEquipment" :key="equipment.id">
                  <div class="equipment-icon">
                    <i :class="equipment.icon"></i>
                  </div>
                  <div class="equipment-content">
                    <h4>{{ equipment.name }}</h4>
                    <p>{{ equipment.description }}</p>
                    <div class="equipment-specs">
                      <div class="spec">
                        <i class="fas fa-ruler"></i>
                        <span>测量范围：{{ equipment.range }}</span>
                      </div>
                      <div class="spec">
                        <i class="fas fa-percentage"></i>
                        <span>精度：{{ equipment.accuracy }}</span>
                      </div>
                    </div>
                    <div class="equipment-tags">
                      <span class="tag" v-for="tag in equipment.tags" :key="tag">{{ tag }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 实验数据 -->
            <div class="experiment-data mt30">
              <div class="section-header">
                <h3><i class="fas fa-database"></i> 实验数据集</h3>
                <div class="data-controls">
                  <input type="text" placeholder="搜索实验数据..." v-model="experimentSearch">
                  <select v-model="experimentSort">
                    <option value="date">按实验日期</option>
                    <option value="type">按流体类型</option>
                    <option value="temperature">按温度</option>
                  </select>
                </div>
              </div>

              <div class="data-grid">
                <div class="data-card" v-for="data in filteredExperimentData" :key="data.id">
                  <div class="data-header">
                    <h4>{{ data.title }}</h4>
                    <span class="data-type" :style="{backgroundColor: data.typeColor}">
                      {{ data.type }}
                    </span>
                  </div>
                  <div class="data-content">
                    <div class="data-meta">
                      <div class="meta-item">
                        <i class="fas fa-thermometer-half"></i>
                        <span>温度：{{ data.temperature }}°C</span>
                      </div>
                      <div class="meta-item">
                        <i class="fas fa-tachometer-alt"></i>
                        <span>流速：{{ data.velocity }} m/s</span>
                      </div>
                    </div>
                    <p>{{ data.description }}</p>
                    <div class="data-stats">
                      <div class="stat">
                        <div class="stat-label">雷诺数</div>
                        <div class="stat-value">{{ data.reynolds }}</div>
                      </div>
                      <div class="stat">
                        <div class="stat-label">弗劳德数</div>
                        <div class="stat-value">{{ data.froude }}</div>
                      </div>
                      <div class="stat">
                        <div class="stat-label">湍流强度</div>
                        <div class="stat-value">{{ data.turbulence }}%</div>
                      </div>
                    </div>
                  </div>
                  <div class="data-footer">
                    <button class="btn-detail" @click="viewExperimentData(data)">
                      <i class="fas fa-chart-line"></i> 数据分析
                    </button>
                    <button class="btn-download" @click="downloadExperimentData(data)">
                      <i class="fas fa-download"></i> 下载数据
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- ==================== 案例分析模块 ==================== -->
          <div class="module-content" v-if="activeModule === 'case'">
            <div class="module-header">
              <h2><i class="fas fa-industry"></i> 工业案例分析</h2>
              <p class="module-desc">冶金工业实际流体力学问题分析与解决方案</p>
            </div>

            <!-- 案例分类 -->
            <div class="case-categories">
              <div class="section-header">
                <h3><i class="fas fa-sitemap"></i> 案例分类</h3>
              </div>
              <div class="category-tabs">
                <div class="tab-item"
                     v-for="category in caseCategories"
                     :key="category.id"
                     :class="{active: activeCaseCategory === category.id}"
                     @click="switchCaseCategory(category.id)">
                  {{ category.name }}
                  <span class="tab-count">{{ category.count }}</span>
                </div>
              </div>
            </div>

            <!-- 案例列表 -->
            <div class="case-studies">
              <div class="case-grid">
                <div class="study-card" v-for="study in filteredCaseStudies" :key="study.id">
                  <div class="study-header">
                    <h4>{{ study.title }}</h4>
                    <div class="study-meta">
                      <span class="meta-item">
                        <i class="fas fa-building"></i> {{ study.company }}
                      </span>
                      <span class="meta-item">
                        <i class="fas fa-calendar"></i> {{ study.year }}
                      </span>
                    </div>
                  </div>
                  <div class="study-content">
                    <p>{{ study.description }}</p>
                    <div class="study-problem">
                      <div class="problem-title">主要问题：</div>
                      <div class="problem-list">
                        <div class="problem-item" v-for="problem in study.problems" :key="problem">
                          <i class="fas fa-exclamation-triangle"></i> {{ problem }}
                        </div>
                      </div>
                    </div>
                    <div class="study-solution">
                      <div class="solution-title">解决方案：</div>
                      <div class="solution-tags">
                        <span class="solution-tag" v-for="solution in study.solutions" :key="solution">
                          {{ solution }}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div class="study-results">
                    <div class="result-item">
                      <div class="result-label">流动改善</div>
                      <div class="result-value">{{ study.results.flowImprovement }}%</div>
                    </div>
                    <div class="result-item">
                      <div class="result-label">能耗降低</div>
                      <div class="result-value">{{ study.results.energyReduction }}%</div>
                    </div>
                    <div class="result-item">
                      <div class="result-label">效率提升</div>
                      <div class="result-value">{{ study.results.efficiency }}%</div>
                    </div>
                  </div>
                  <div class="study-footer">
                    <button class="btn-detail" @click="viewCaseStudy(study)">
                      <i class="fas fa-book-open"></i> 案例详情
                    </button>
                    <button class="btn-report" @click="downloadCaseReport(study)">
                      <i class="fas fa-file-pdf"></i> 技术报告
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- ==================== 计算工具模块 ==================== -->
          <div class="module-content" v-if="activeModule === 'tools'">
            <div class="module-header">
              <h2><i class="fas fa-calculator"></i> 在线计算工具</h2>
              <p class="module-desc">冶金流体力学在线计算与分析工具</p>
            </div>

            <!-- 工具分类 -->
            <div class="tool-categories">
              <div class="section-header">
                <h3><i class="fas fa-toolbox"></i> 计算工具分类</h3>
              </div>
              <div class="categories-grid">
                <div class="tool-category-card" v-for="tool in calculationTools" :key="tool.id"
                     :class="{active: activeTool === tool.id}"
                     @click="switchTool(tool.id)">
                  <div class="tool-icon">
                    <i :class="tool.icon"></i>
                  </div>
                  <div class="tool-content">
                    <h4>{{ tool.name }}</h4>
                    <p>{{ tool.description }}</p>
                    <div class="tool-features">
                      <span class="feature" v-for="feature in tool.features" :key="feature">{{ feature }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 在线计算器 -->
            <div class="online-calculator mt30" v-if="activeTool">
              <div class="section-header">
                <h3><i class="fas fa-calculator"></i> {{ activeToolConfig.name }}计算器</h3>
              </div>

              <div class="calculator-container">
                <div class="calculator-inputs">
                  <div class="input-group" v-for="input in activeToolConfig.inputs" :key="input.id">
                    <label :for="input.id">
                      <i :class="input.icon"></i> {{ input.label }}
                    </label>
                    <input :type="input.type" :id="input.id" v-model="calculatorInputs[input.id]"
                           :placeholder="input.placeholder" :step="input.step">
                    <span class="unit">{{ input.unit }}</span>
                  </div>
                </div>

                <div class="calculator-results">
                  <div class="result-header">
                    <h4>计算结果</h4>
                    <button class="btn-calculate" @click="calculateTool">
                      <i class="fas fa-calculator"></i> 计算
                    </button>
                  </div>

                  <div class="result-content" v-if="calculationResult">
                    <div class="result-item" v-for="result in calculationResult.results" :key="result.name">
                      <div class="result-label">{{ result.label }}</div>
                      <div class="result-value">{{ result.value }} <span class="result-unit">{{ result.unit }}</span></div>
                    </div>

                    <div class="result-analysis" v-if="calculationResult.analysis">
                      <div class="analysis-title">结果分析：</div>
                      <p>{{ calculationResult.analysis }}</p>
                    </div>
                  </div>

                  <div class="result-empty" v-else>
                    <i class="fas fa-calculator"></i>
                    <p>输入参数并点击"计算"按钮获取结果</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <Footer></Footer>
</template>

<script>
import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";

export default {
  name: "FluidDynamics",
  components: {
    Header,
    Footer,
  },
  data() {
    return {
      activeModule: 'overview',
      searchParams: {
        fluidType: '',
        property: '',
        tempMin: '',
        tempMax: ''
      },
      showResults: false,
      fluidResults: [],
      currentPage: 1,
      pageSize: 10,

      // 流体分类数据
      fluidCategories: [
        {
          id: 'steel',
          name: '钢液',
          icon: 'fas fa-fire',
          color: '#FF6B6B',
          description: '高温钢液的流动特性与物性参数',
          dataCount: '2,850+',
          tempRange: '1500-1700°C'
        },
        {
          id: 'iron',
          name: '铁水',
          icon: 'fas fa-industry',
          color: '#0046DB',
          description: '高炉铁水流体力学特性',
          dataCount: '1,650+',
          tempRange: '1300-1500°C'
        },
        {
          id: 'slag',
          name: '熔渣',
          icon: 'fas fa-volcano',
          color: '#4ECDC4',
          description: '冶金熔渣的粘度与表面张力',
          dataCount: '1,250+',
          tempRange: '1400-1600°C'
        },
        {
          id: 'gas',
          name: '煤气',
          icon: 'fas fa-wind',
          color: '#96CEB4',
          description: '冶金煤气流动与燃烧特性',
          dataCount: '2,750+',
          tempRange: '20-2000°C'
        }
      ],

      // 模拟案例数据
      simulationCases: [
        {
          id: 1,
          title: 'RH精炼循环流模拟',
          type: '钢液流动',
          bgColor: '#0046DB',
          tagColor: '#0046DB',
          description: 'RH真空精炼装置内钢液循环流动特性分析',
          meshCount: '850,000',
          computeTime: '8小时',
          arrows: [
            { id: 1, style: 'left: 20%; top: 30%; transform: rotate(45deg)' },
            { id: 2, style: 'left: 40%; top: 50%; transform: rotate(-30deg)' },
            { id: 3, style: 'left: 60%; top: 20%; transform: rotate(60deg)' },
            { id: 4, style: 'left: 30%; top: 70%; transform: rotate(-15deg)' }
          ]
        },
        {
          id: 2,
          title: '高炉风口回旋区模拟',
          type: '气固两相',
          bgColor: '#FF6B6B',
          tagColor: '#FF6B6B',
          description: '高炉风口回旋区气体-焦炭颗粒流动模拟',
          meshCount: '1,200,000',
          computeTime: '12小时',
          arrows: [
            { id: 1, style: 'left: 30%; top: 40%; transform: rotate(90deg)' },
            { id: 2, style: 'left: 50%; top: 20%; transform: rotate(120deg)' },
            { id: 3, style: 'left: 70%; top: 60%; transform: rotate(-60deg)' }
          ]
        }
      ],

      simulationParams: {
        model: 'rans',
        meshSize: 100000,
        timeStep: 0.01,
        tempMin: 1500,
        tempMax: 1600
      },

      // 实验设备数据
      experimentEquipment: [
        {
          id: 1,
          name: '激光多普勒测速仪',
          icon: 'fas fa-tachometer-alt',
          description: '非接触式流体速度测量设备',
          range: '0.001-100 m/s',
          accuracy: '±1%',
          tags: ['非接触', '高精度', '实时测量']
        },
        {
          id: 2,
          name: '粒子图像测速系统',
          icon: 'fas fa-camera',
          description: '全场速度测量与流场可视化',
          range: '0.01-10 m/s',
          accuracy: '±2%',
          tags: ['全场测量', '可视化', '瞬态分析']
        }
      ],

      experimentSearch: '',
      experimentSort: 'date',

      // 案例分析数据
      activeCaseCategory: 'all',
      caseCategories: [
        { id: 'all', name: '全部案例', count: 85 },
        { id: 'flow', name: '流动优化', count: 32 },
        { id: 'mixing', name: '混合搅拌', count: 18 },
        { id: 'heat', name: '传热强化', count: 15 },
        { id: 'reaction', name: '反应器', count: 20 }
      ],

      // 计算工具数据
      activeTool: 'reynolds',
      calculationTools: [
        {
          id: 'reynolds',
          name: '雷诺数计算',
          icon: 'fas fa-water',
          description: '计算流体流动状态与湍流特性',
          features: ['层流/湍流判断', '临界流速', '相似准则']
        },
        {
          id: 'froude',
          name: '弗劳德数计算',
          icon: 'fas fa-tint',
          description: '重力对流动影响的无量纲数',
          features: ['重力相似', '自由表面流', '水力学']
        },
        {
          id: 'pressure',
          name: '压力损失计算',
          icon: 'fas fa-compress-alt',
          description: '管道与设备压力损失计算',
          features: ['摩擦损失', '局部损失', '系统阻力']
        }
      ],

      calculatorInputs: {},
      calculationResult: null
    };
  },
  computed: {
    totalPages() {
      return Math.ceil(this.fluidResults.length / this.pageSize);
    },
    paginatedResults() {
      const start = (this.currentPage - 1) * this.pageSize;
      const end = start + this.pageSize;
      return this.fluidResults.slice(start, end);
    },

    filteredExperimentData() {
      // 模拟过滤逻辑
      return [
        {
          id: 1,
          title: '钢液连铸结晶器流场',
          type: '钢液流动',
          typeColor: '#0046DB',
          temperature: 1550,
          velocity: 1.2,
          description: '连铸结晶器内钢液流动特性实验测量',
          reynolds: '1.2e5',
          froude: '0.15',
          turbulence: '12.5'
        },
        {
          id: 2,
          title: 'RH真空精炼循环流',
          type: '钢液搅拌',
          typeColor: '#FF6B6B',
          temperature: 1600,
          velocity: 2.5,
          description: 'RH精炼装置钢液循环流动实验',
          reynolds: '3.5e5',
          froude: '0.08',
          turbulence: '8.7'
        }
      ];
    },

    filteredCaseStudies() {
      return [
        {
          id: 1,
          title: '转炉底吹优化改造',
          company: '某钢铁集团',
          year: '2023',
          description: '通过数值模拟优化转炉底吹布置，提高钢液混合效率',
          problems: ['底吹位置不合理', '钢液混合不均匀', '搅拌效果差'],
          solutions: ['优化底吹布置', '调整气体流量', '改进控制系统'],
          results: {
            flowImprovement: 45,
            energyReduction: 18,
            efficiency: 32
          }
        }
      ];
    },

    activeToolConfig() {
      const tools = {
        reynolds: {
          name: '雷诺数',
          inputs: [
            {
              id: 'velocity',
              label: '流速',
              type: 'number',
              placeholder: '输入流速',
              unit: 'm/s',
              step: 0.1,
              icon: 'fas fa-tachometer-alt'
            },
            {
              id: 'diameter',
              label: '特征长度',
              type: 'number',
              placeholder: '输入直径或长度',
              unit: 'm',
              step: 0.01,
              icon: 'fas fa-ruler'
            },
            {
              id: 'density',
              label: '密度',
              type: 'number',
              placeholder: '输入流体密度',
              unit: 'kg/m³',
              step: 1,
              icon: 'fas fa-weight'
            },
            {
              id: 'viscosity',
              label: '粘度',
              type: 'number',
              placeholder: '输入动力粘度',
              unit: 'Pa·s',
              step: 0.001,
              icon: 'fas fa-water'
            }
          ]
        }
      };
      return tools[this.activeTool] || tools.reynolds;
    }
  },
  methods: {
    switchModule(module) {
      this.activeModule = module;
      if (module === 'database') {
        this.searchFluidData();
      }
    },

    searchFluidData() {
      this.showResults = true;
      this.currentPage = 1;

      // 模拟数据
      this.fluidResults = [
        {
          type: '钢液',
          temperature: 1550,
          density: 7020,
          viscosity: 0.0056,
          conductivity: 40.5,
          specificHeat: 800,
          source: '实验测定'
        },
        {
          type: '钢液',
          temperature: 1600,
          density: 7000,
          viscosity: 0.0048,
          conductivity: 42.3,
          specificHeat: 820,
          source: '数值计算'
        },
        {
          type: '铁水',
          temperature: 1400,
          density: 6980,
          viscosity: 0.0065,
          conductivity: 38.7,
          specificHeat: 780,
          source: '文献数据'
        },
        {
          type: '熔渣',
          temperature: 1500,
          density: 2800,
          viscosity: 0.15,
          conductivity: 1.2,
          specificHeat: 1250,
          source: '实验测定'
        }
      ];
    },

    resetSearch() {
      this.searchParams = {
        fluidType: '',
        property: '',
        tempMin: '',
        tempMax: ''
      };
      this.showResults = false;
      this.fluidResults = [];
      this.currentPage = 1;
    },

    exportData() {
      alert('数据导出功能开发中...');
    },

    viewFluidDetail(item) {
      alert(`流体详情：
      类型：${item.type}
      温度：${item.temperature}°C
      密度：${item.density} kg/m³
      粘度：${item.viscosity} Pa·s
      导热系数：${item.conductivity} W/m·K
      比热容：${item.specificHeat} J/kg·K
      数据来源：${item.source}`);
    },

    viewSimulationDetail(caseItem) {
      alert(`运行模拟：${caseItem.title}
      开始模拟计算，请等待结果...`);
    },

    viewCaseResults(caseItem) {
      alert(`查看模拟结果：${caseItem.title}
      正在加载计算结果...`);
    },

    runSimulation() {
      alert(`开始模拟计算：
      模型：${this.simulationParams.model}
      网格数量：${this.simulationParams.meshSize}
      时间步长：${this.simulationParams.timeStep}s
      温度范围：${this.simulationParams.tempMin}-${this.simulationParams.tempMax}°C
      计算正在进行中...`);
    },

    saveSimulationConfig() {
      alert('模拟配置已保存');
    },

    switchCaseCategory(category) {
      this.activeCaseCategory = category;
    },

    switchTool(toolId) {
      this.activeTool = toolId;
      this.calculationResult = null;
      this.calculatorInputs = {};
    },

    calculateTool() {
      if (this.activeTool === 'reynolds') {
        const v = parseFloat(this.calculatorInputs.velocity) || 1;
        const d = parseFloat(this.calculatorInputs.diameter) || 0.1;
        const rho = parseFloat(this.calculatorInputs.density) || 1000;
        const mu = parseFloat(this.calculatorInputs.viscosity) || 0.001;

        const Re = (v * d * rho) / mu;

        let flowType = '层流';
        let analysis = '';

        if (Re < 2000) {
          flowType = '层流';
          analysis = '流动处于层流状态，流线平滑，分子扩散占主导';
        } else if (Re < 4000) {
          flowType = '过渡流';
          analysis = '流动处于过渡状态，可能发生层流向湍流转捩';
        } else {
          flowType = '湍流';
          analysis = '流动处于湍流状态，存在强烈脉动和混合';
        }

        this.calculationResult = {
          results: [
            { label: '雷诺数(Re)', value: Re.toFixed(2), unit: '' },
            { label: '流动状态', value: flowType, unit: '' },
            { label: '临界流速', value: ((2000 * mu) / (d * rho)).toFixed(3), unit: 'm/s' }
          ],
          analysis: analysis
        };
      }
    },

    viewExperimentData(data) {
      alert(`实验数据分析：${data.title}
      正在生成分析图表...`);
    },

    downloadExperimentData(data) {
      alert(`下载实验数据：${data.title}
      文件正在下载中...`);
    },

    viewCaseStudy(study) {
      alert(`查看案例详情：${study.title}
      正在加载详细报告...`);
    },

    downloadCaseReport(study) {
      alert(`下载技术报告：${study.title}
      PDF文件正在生成...`);
    }
  },
  mounted() {
    // 移动端菜单切换
    const menuBtn = document.querySelector('.m-nav-but');
    const leftNav = document.querySelector('.data-aggregation-left');

    if (menuBtn && leftNav) {
      menuBtn.addEventListener('click', function() {
        const leftP = getComputedStyle(leftNav).left;
        if (leftP === '0px') {
          leftNav.style.left = '-220px';
          this.textContent = '点击展开菜单';
        } else {
          leftNav.style.left = '0px';
          this.textContent = '点击隐藏菜单';
        }
      });
    }
  }
};
</script>

<style scoped>
/* ==================== 基础样式 ==================== */
.fluid-dynamics {
  background-color: #f5f7fa;
  min-height: 120vh;
  font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
  display: flex;
  flex-direction: column;
  padding-top: 80px;
}

.container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 15px;
}

.main-content {
  padding: 40px 0 30px;
  flex: 1;
}

/* ==================== 网格布局 ==================== */
.data-aggregation {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 24px;
  align-items: stretch;
}

/* ==================== 左侧导航栏 ==================== */
.data-aggregation-left {
  grid-column: 1;
  position: relative;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  overflow: hidden;
  display: flex;
  flex-direction: column;
  height: auto;
  min-height: 0;
}

.left-sub-nav-box {
  width: 100%;
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  background: #fff;
  min-height: 200px;
}

.data-aggregation-nav {
  width: 100%;
  border-radius: 0;
  overflow: hidden;
  margin-bottom: 0;
  transition: all 0.3s;
  border-bottom: 1px solid #f0f0f0;
}

.data-aggregation-nav:last-child {
  border-bottom: none;
}

.data-aggregation-nav dt {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  height: 56px;
  font-size: 16px;
  color: #333;
  background-color: #fff;
  padding-left: 20px;
  cursor: pointer;
  position: relative;
  transition: all 0.3s;
  border-left: 3px solid transparent;
}

.data-aggregation-nav dt:hover {
  background-color: #f8f9fa;
  color: #0046DB;
}

.data-aggregation-nav dt.active {
  background-color: #f0f7ff;
  color: #0046DB;
  border-left-color: #0046DB;
  font-weight: 600;
}

.data-aggregation-nav dt::before {
  content: '';
  position: absolute;
  left: 20px;
  width: 16px;
  height: 16px;
  background-color: #666;
  mask-size: contain;
  mask-repeat: no-repeat;
  mask-position: center;
  transition: all 0.3s;
}

.data-aggregation-nav dt:hover::before,
.data-aggregation-nav dt.active::before {
  background-color: #0046DB;
}

/* 导航图标 */
.data-aggregation-nav dt.index1::before {
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M12 2L4 5v6.09c0 5.05 3.41 9.76 8 10.91 4.59-1.15 8-5.86 8-10.91V5l-8-3zm0 2l6 1.83-6 1.82-6-1.82L12 4zm0 7c1.65 0 3 1.35 3 3s-1.35 3-3 3-3-1.35-3-3 1.35-3 3-3z'/%3E%3C/svg%3E");
}

.data-aggregation-nav dt.index2::before {
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-9 14l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z'/%3E%3C/svg%3E");
}

.data-aggregation-nav dt.index3::before {
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M12 2C8.13 2 5 5.13 5 9c0 5.25 7 13 7 13s7-7.75 7-13c0-3.87-3.13-7-7-7zm0 2.5c1.93 0 3.5 1.57 3.5 3.5s-1.57 3.5-3.5 3.5S8.5 9.93 8.5 8s1.57-3.5 3.5-3.5z'/%3E%3C/svg%3E");
}

.data-aggregation-nav dt.index4::before {
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M19.36 2.72l1.42 1.42-5.72 5.71c1.07 1.54 1.22 3.39.32 4.59L9.06 8.12c1.2-.9 3.05-.75 4.59.32l5.71-5.72zM5.93 17.57c-2.01-2.01-3.24-4.41-3.58-6.71l4.71 4.7 2.53-.51-2.49-2.49-.51 2.49-4.7-4.71c.3-2.17 1.55-4.57 3.59-6.61 3.43-3.43 8.64-3.43 12.07 0 3.43 3.43 3.43 8.64 0 12.07-2.04 2.04-4.44 3.29-6.61 3.59l-4.71-4.7-2.52.51 2.49 2.49.51-2.49 4.7 4.71c-2.3-.34-4.7-1.57-6.71-3.58z'/%3E%3C/svg%3E");
}

.data-aggregation-nav dt.index5::before {
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-9 14l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z'/%3E%3C/svg%3E");
}

.data-aggregation-nav dt.index6::before {
  mask-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'%3E%3Cpath d='M14 2H6c-1.1 0-1.99.9-1.99 2L4 20c0 1.1.89 2 1.99 2H18c1.1 0 2-.9 2-2V8l-6-6zm2 16H8v-2h8v2zm0-4H8v-2h8v2zm-3-5V3.5L18.5 9H13z'/%3E%3C/svg%3E");
}

.data-aggregation-nav dt a {
  color: inherit;
  text-decoration: none;
  flex: 1;
  padding-left: 24px;
  display: flex;
  align-items: center;
  height: 100%;
}

.m-nav-but {
  display: none;
  position: absolute;
  top: 10px;
  right: -40px;
  width: 30px;
  height: 30px;
  background-color: #0046DB;
  color: #fff;
  font-size: 12px;
  text-align: center;
  line-height: 30px;
  cursor: pointer;
  border-radius: 4px;
  z-index: 100;
  box-shadow: 0 2px 8px rgba(0, 70, 219, 0.3);
}

/* ==================== 右侧内容区域 ==================== */
.data-aggregation-right {
  grid-column: 2;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.module-content {
  background: #fff;
  border-radius: 12px;
  padding: 25px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  min-height: auto;
  flex: 1;
  display: flex;
  flex-direction: column;
  border: 1px solid transparent;
  transition: all 0.3s;
}

.module-content:hover {
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.1);
  border-color: #f0f0f0;
}

.module-header {
  margin-bottom: 20px;
  padding-bottom: 15px;
  border-bottom: 1px solid #e8e8e8;
}

.module-header h2 {
  font-size: 22px;
  color: #333;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.module-header h2 i {
  color: #0046DB;
  font-size: 20px;
}

.module-desc {
  font-size: 14px;
  color: #666;
  margin: 0;
  line-height: 1.5;
}

/* ==================== 数据卡片 ==================== */
.echarts-data-num {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
  margin-bottom: 20px;
}

.data-item {
  display: flex;
  justify-content: space-between;
  padding: 18px;
  background: #fff;
  border-radius: 10px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all 0.3s;
  border: 1px solid #f0f0f0;
}

.data-item:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #0046DB;
}

.data-item dl {
  flex: 1;
}

.data-item dt {
  font-size: 13px;
  color: #666;
  margin-bottom: 6px;
  font-weight: 500;
}

.data-item dd {
  font-size: 20px;
  font-weight: 700;
  color: #0046DB;
  margin: 0;
  line-height: 1.2;
}

.data-item .trend {
  font-size: 12px;
  font-weight: normal;
  margin-top: 4px;
}

.data-item .trend.up {
  color: #f56c6c;
}

.data-item .trend.down {
  color: #67c23a;
}

.card-icon {
  width: 48px;
  height: 48px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #0046DB;
}

/* ==================== 应用场景 ==================== */
.application-scenarios {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
}

.scenarios-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.scenario-card {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 15px;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.scenario-card:hover {
  background: #e6f7ff;
  border-color: #0046DB;
  transform: translateY(-2px);
}

.scenario-icon {
  font-size: 28px;
  color: #0046DB;
  margin-bottom: 10px;
}

.scenario-content h4 {
  font-size: 15px;
  color: #333;
  margin: 0 0 6px 0;
}

.scenario-content p {
  font-size: 13px;
  color: #666;
  margin: 0 0 10px 0;
  line-height: 1.4;
}

.scenario-tags {
  display: flex;
  gap: 5px;
}

.tag {
  font-size: 10px;
  color: #0046DB;
  background: rgba(0, 70, 219, 0.1);
  padding: 2px 6px;
  border-radius: 10px;
}

/* ==================== 搜索区域 ==================== */
.search-section {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  margin-bottom: 20px;
  border: 1px solid #f0f0f0;
}

.section-header {
  margin-bottom: 15px;
}

.section-header h3 {
  font-size: 18px;
  color: #333;
  margin: 0 0 6px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-header h3 i {
  color: #0046DB;
}

.section-header p {
  color: #666;
  font-size: 13px;
  margin: 0;
}

.search-form {
  width: 100%;
}

.form-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
  margin-bottom: 25px;
}

.form-group {
  display: flex;
  flex-direction: column;
}

.form-group label {
  color: #666;
  margin-bottom: 8px;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.form-group label i {
  color: #0046DB;
}

.form-group select,
.form-group input {
  padding: 12px 15px;
  background: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  color: #333;
  font-size: 14px;
  transition: all 0.3s;
}

.form-group select:focus,
.form-group input:focus {
  outline: none;
  border-color: #0046DB;
  background: #fff;
}

.range-input {
  display: flex;
  align-items: center;
  gap: 10px;
}

.range-input input {
  flex: 1;
}

.range-input span {
  color: #666;
  font-size: 14px;
}

.form-actions {
  display: flex;
  gap: 15px;
}

.btn-search,
.btn-reset {
  padding: 12px 25px;
  border-radius: 30px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-search {
  background: #0046DB;
  color: #fff;
  border: 1px solid #0046DB;
}

.btn-search:hover {
  background: #003db9;
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 70, 219, 0.3);
}

.btn-reset {
  background: transparent;
  color: #666;
  border: 1px solid #dcdfe6;
}

.btn-reset:hover {
  background: #f8f9fa;
  color: #333;
}

/* ==================== 数据结果表格 ==================== */
.data-results {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.results-header h3 {
  font-size: 18px;
  color: #333;
  display: flex;
  align-items: center;
  gap: 8px;
}

.results-header h3 i {
  color: #0046DB;
}

.results-info {
  display: flex;
  align-items: center;
  gap: 20px;
}

.results-info span {
  color: #666;
  font-size: 14px;
}

.btn-export {
  padding: 8px 16px;
  background: rgba(0, 70, 219, 0.1);
  border: 1px solid rgba(0, 70, 219, 0.3);
  border-radius: 20px;
  color: #0046DB;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-export:hover {
  background: rgba(0, 70, 219, 0.2);
  color: #003db9;
}

.results-table {
  overflow-x: auto;
}

.results-table table {
  width: 100%;
  border-collapse: collapse;
  min-width: 800px;
}

.results-table thead {
  background: #fafafa;
}

.results-table th {
  padding: 14px;
  text-align: left;
  color: #666;
  font-weight: 500;
  font-size: 13px;
  border-bottom: 1px solid #e8e8e8;
}

.results-table td {
  padding: 12px;
  color: #333;
  font-size: 13px;
  border-bottom: 1px solid #e8e8e8;
}

.results-table tbody tr:hover {
  background: #f8f9fa;
}

.value-cell {
  color: #0046DB;
  font-weight: 500;
}

.btn-detail {
  padding: 6px 12px;
  background: transparent;
  border: 1px solid #dcdfe6;
  border-radius: 15px;
  color: #666;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 5px;
}

.btn-detail:hover {
  background: rgba(0, 70, 219, 0.1);
  color: #0046DB;
  border-color: rgba(0, 70, 219, 0.3);
}

/* ==================== 流体分类 ==================== */
.fluid-categories {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
}

.categories-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.category-card {
  background: #fff;
  border-radius: 8px;
  padding: 15px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  transition: all 0.3s;
  border: 1px solid #f0f0f0;
}

.category-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #0046DB;
}

.category-icon {
  width: 50px;
  height: 50px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 15px;
  color: white;
  font-size: 24px;
}

.category-content h4 {
  font-size: 16px;
  color: #333;
  margin: 0 0 8px 0;
}

.category-content p {
  font-size: 13px;
  color: #666;
  margin: 0 0 12px 0;
  line-height: 1.4;
}

.category-stats {
  display: flex;
  gap: 15px;
}

.stat {
  display: flex;
  flex-direction: column;
}

.stat-label {
  font-size: 11px;
  color: #999;
  margin-bottom: 2px;
}

.stat-value {
  font-size: 14px;
  font-weight: 600;
  color: #0046DB;
}

/* ==================== 模拟案例 ==================== */
.simulation-cases {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
}

.cases-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 20px;
}

.case-card {
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  padding: 15px;
  transition: all 0.3s;
}

.case-card:hover {
  background: #e6f7ff;
  transform: translateY(-2px);
}

.case-visual {
  width: 200px;
  height: 150px;
  border-radius: 6px;
  overflow: hidden;
}

.mock-flow-visualization {
  width: 100%;
  height: 100%;
  position: relative;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.flow-arrow {
  position: absolute;
  width: 30px;
  height: 30px;
  background: rgba(255, 255, 255, 0.8);
  clip-path: polygon(0% 0%, 100% 50%, 0% 100%);
}

.case-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.case-header h4 {
  font-size: 16px;
  color: #333;
  margin: 0;
}

.case-tag {
  font-size: 10px;
  color: #fff;
  padding: 2px 8px;
  border-radius: 10px;
}

.case-card p {
  font-size: 13px;
  color: #666;
  margin: 0 0 12px 0;
  line-height: 1.4;
}

.case-meta {
  display: flex;
  gap: 15px;
  margin-bottom: 15px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: #666;
}

.meta-item i {
  color: #0046DB;
}

.case-actions {
  display: flex;
  gap: 10px;
}

.btn-case {
  padding: 6px 12px;
  background: transparent;
  border: 1px solid #dcdfe6;
  border-radius: 15px;
  color: #666;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 5px;
}

.btn-case:hover {
  background: rgba(0, 180, 255, 0.1);
  color: #00B4FF;
  border-color: rgba(0, 180, 255, 0.3);
}

/* ==================== 模拟参数设置 ==================== */
.simulation-params {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
}

.params-form {
  width: 100%;
}

.params-row {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 20px;
}

.param-group {
  display: flex;
  flex-direction: column;
}

.param-group label {
  color: #666;
  margin-bottom: 8px;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.param-group label i {
  color: #0046DB;
}

.param-group select,
.param-group input[type="number"] {
  padding: 10px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
}

.param-group input[type="range"] {
  flex: 1;
  margin: 10px 0;
}

.param-value {
  font-size: 12px;
  color: #666;
  text-align: right;
}

.params-actions {
  display: flex;
  gap: 15px;
}

.btn-run,
.btn-save {
  padding: 12px 25px;
  border-radius: 30px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 8px;
}

.btn-run {
  background: #0046DB;
  color: #fff;
  border: 1px solid #0046DB;
}

.btn-run:hover {
  background: #003db9;
  transform: translateY(-2px);
  box-shadow: 0 5px 15px rgba(0, 70, 219, 0.3);
}

.btn-save {
  background: transparent;
  color: #666;
  border: 1px solid #dcdfe6;
}

.btn-save:hover {
  background: #f8f9fa;
  color: #333;
}

/* ==================== 实验设备 ==================== */
.experiment-equipment {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
}

.equipment-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.equipment-card {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 15px;
  transition: all 0.3s;
}

.equipment-card:hover {
  background: #e6f7ff;
  transform: translateY(-2px);
}

.equipment-icon {
  font-size: 32px;
  color: #0046DB;
  margin-bottom: 10px;
}

.equipment-content h4 {
  font-size: 15px;
  color: #333;
  margin: 0 0 8px 0;
}

.equipment-content p {
  font-size: 13px;
  color: #666;
  margin: 0 0 10px 0;
  line-height: 1.4;
}

.equipment-specs {
  display: flex;
  gap: 10px;
  margin-bottom: 10px;
}

.spec {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #666;
}

.spec i {
  color: #0046DB;
}

.equipment-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

/* ==================== 实验数据 ==================== */
.experiment-data {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
}

.data-controls {
  display: flex;
  gap: 10px;
  align-items: center;
}

.data-controls input {
  padding: 8px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
  flex: 1;
  max-width: 300px;
}

.data-controls select {
  padding: 8px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
  background: #fff;
  cursor: pointer;
}

.data-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
  margin-top: 15px;
}

.data-card {
  background: #fff;
  border-radius: 6px;
  padding: 15px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
  transition: all 0.3s;
}

.data-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #0046DB;
}

.data-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.data-header h4 {
  font-size: 15px;
  color: #333;
  margin: 0;
  flex: 1;
}

.data-type {
  font-size: 10px;
  color: #fff;
  padding: 2px 6px;
  border-radius: 10px;
}

.data-meta {
  display: flex;
  gap: 10px;
  margin-bottom: 8px;
}

.data-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin: 10px 0;
}

.stat-label {
  font-size: 11px;
  color: #999;
  margin-bottom: 2px;
}

.stat-value {
  font-size: 14px;
  font-weight: 600;
  color: #0046DB;
}

.data-footer {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.btn-download {
  padding: 6px 12px;
  background: transparent;
  border: 1px solid #dcdfe6;
  border-radius: 15px;
  color: #666;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 5px;
}

.btn-download:hover {
  background: rgba(76, 175, 80, 0.1);
  color: #4CAF50;
  border-color: rgba(76, 175, 80, 0.3);
}

/* ==================== 案例分析 ==================== */
.case-categories {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  margin-bottom: 15px;
  border: 1px solid #f0f0f0;
}

.category-tabs {
  display: flex;
  gap: 8px;
  overflow-x: auto;
  padding-bottom: 5px;
}

.tab-item {
  padding: 8px 15px;
  background: #f8f9fa;
  border-radius: 6px;
  cursor: pointer;
  font-size: 13px;
  color: #666;
  display: flex;
  align-items: center;
  gap: 6px;
  transition: all 0.3s;
  white-space: nowrap;
}

.tab-item:hover,
.tab-item.active {
  background: #0046DB;
  color: #fff;
}

.tab-count {
  font-size: 11px;
  background: rgba(255, 255, 255, 0.2);
  padding: 2px 5px;
  border-radius: 8px;
}

.case-studies {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
}

.case-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 15px;
}

.study-card {
  background: #fff;
  border-radius: 6px;
  padding: 15px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
  transition: all 0.3s;
}

.study-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #0046DB;
}

.study-header {
  margin-bottom: 10px;
}

.study-header h4 {
  font-size: 16px;
  color: #333;
  margin: 0 0 5px 0;
}

.study-meta {
  display: flex;
  gap: 10px;
  font-size: 12px;
  color: #666;
}

.study-problem,
.study-solution {
  margin: 10px 0;
}

.problem-title,
.solution-title {
  font-size: 13px;
  color: #333;
  font-weight: 500;
  margin-bottom: 5px;
}

.problem-list {
  margin-left: 15px;
}

.problem-item {
  font-size: 12px;
  color: #666;
  margin-bottom: 3px;
  display: flex;
  align-items: center;
  gap: 5px;
}

.problem-item i {
  color: #FF6B6B;
}

.solution-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
}

.solution-tag {
  font-size: 10px;
  color: #0046DB;
  background: rgba(0, 70, 219, 0.1);
  padding: 2px 6px;
  border-radius: 10px;
}

.study-results {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin: 15px 0;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 6px;
}

.result-item {
  text-align: center;
}

.result-label {
  font-size: 11px;
  color: #666;
  margin-bottom: 2px;
}

.result-value {
  font-size: 18px;
  font-weight: 700;
  color: #0046DB;
}

.study-footer {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.btn-report {
  padding: 6px 12px;
  background: transparent;
  border: 1px solid #dcdfe6;
  border-radius: 15px;
  color: #666;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 5px;
}

.btn-report:hover {
  background: rgba(255, 107, 107, 0.1);
  color: #FF6B6B;
  border-color: rgba(255, 107, 107, 0.3);
}

/* ==================== 计算工具 ==================== */
.tool-categories {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
}

.tool-category-card {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 15px;
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.tool-category-card:hover,
.tool-category-card.active {
  background: #e6f7ff;
  border-color: #0046DB;
  transform: translateY(-2px);
}

.tool-icon {
  font-size: 28px;
  color: #0046DB;
  margin-bottom: 10px;
}

.tool-content h4 {
  font-size: 15px;
  color: #333;
  margin: 0 0 6px 0;
}

.tool-content p {
  font-size: 13px;
  color: #666;
  margin: 0 0 10px 0;
  line-height: 1.4;
}

.tool-features {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.feature {
  font-size: 10px;
  color: #666;
  background: rgba(0, 0, 0, 0.05);
  padding: 2px 5px;
  border-radius: 3px;
}

.online-calculator {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
}

.calculator-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
  margin-top: 15px;
}

.calculator-inputs {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.input-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.input-group label {
  width: 120px;
  color: #666;
  font-size: 14px;
  display: flex;
  align-items: center;
  gap: 5px;
}

.input-group input {
  flex: 1;
  padding: 10px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 14px;
}

.unit {
  width: 40px;
  color: #666;
  font-size: 14px;
}

.calculator-results {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 15px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #e8e8e8;
}

.result-header h4 {
  font-size: 16px;
  color: #333;
  margin: 0;
}

.btn-calculate {
  padding: 8px 16px;
  background: #0046DB;
  color: #fff;
  border: none;
  border-radius: 20px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 5px;
}

.btn-calculate:hover {
  background: #003db9;
}

.result-content {
  min-height: 200px;
}

.result-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #e8e8e8;
}

.result-label {
  font-size: 14px;
  color: #666;
}

.result-value {
  font-size: 16px;
  font-weight: 600;
  color: #0046DB;
}

.result-unit {
  font-size: 12px;
  color: #999;
  margin-left: 2px;
}

.result-analysis {
  margin-top: 15px;
  padding: 10px;
  background: #e6f7ff;
  border-radius: 4px;
}

.analysis-title {
  font-size: 13px;
  color: #0046DB;
  font-weight: 500;
  margin-bottom: 5px;
}

.result-empty {
  height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #999;
}

.result-empty i {
  font-size: 48px;
  margin-bottom: 10px;
  opacity: 0.5;
}

/* ==================== 分页 ==================== */
.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-top: 30px;
  padding-top: 20px;
  border-top: 1px solid #e8e8e8;
}

.page-btn {
  padding: 8px 16px;
  background: #fff;
  border: 1px solid #dcdfe6;
  border-radius: 20px;
  color: #666;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 5px;
}

.page-btn:hover:not(:disabled) {
  background: #f8f9fa;
  color: #333;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  color: #666;
  font-size: 14px;
}

/* ==================== 响应式设计 ==================== */
@media (max-width: 1200px) {
  .container {
    max-width: 960px;
  }

  .echarts-data-num {
    grid-template-columns: repeat(2, 1fr);
  }

  .scenarios-grid {
    grid-template-columns: 1fr;
  }

  .categories-grid {
    grid-template-columns: 1fr;
  }

  .data-grid {
    grid-template-columns: 1fr;
  }

  .calculator-container {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 992px) {
  .data-aggregation {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto;
    gap: 15px;
  }

  .data-aggregation-left {
    grid-column: 1;
    grid-row: 1;
    width: 100%;
    height: auto;
    min-height: auto;
  }

  .data-aggregation-right {
    grid-column: 1;
    grid-row: 2;
    width: 100%;
    height: auto;
  }

  .m-nav-but {
    display: block;
  }

  .fluid-dynamics {
    padding-top: 80px;
  }

  .case-card {
    grid-template-columns: 1fr;
  }

  .case-visual {
    width: 100%;
    height: 120px;
  }
}

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }

  .params-row {
    grid-template-columns: 1fr;
  }

  .equipment-grid {
    grid-template-columns: 1fr;
  }

  .study-results {
    grid-template-columns: 1fr;
    gap: 15px;
  }

  .main-content {
    padding: 15px 0 25px;
  }

  .module-content {
    padding: 15px;
  }

  .echarts-data-num {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .module-header h2 {
    font-size: 18px;
  }

  .data-item {
    padding: 15px;
  }

  .data-item dd {
    font-size: 18px;
  }
}

@media (max-width: 576px) {
  .container {
    padding: 0 10px;
  }

  .module-header h2 {
    font-size: 16px;
  }

  .data-item {
    padding: 12px;
  }

  .form-actions {
    flex-wrap: wrap;
  }

  .btn-search,
  .btn-reset {
    flex: 1;
    min-width: 120px;
  }

  .results-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .results-info {
    width: 100%;
    justify-content: space-between;
  }

  .input-group {
    flex-direction: column;
    align-items: flex-start;
  }

  .input-group label {
    width: 100%;
  }

  .input-group input {
    width: 100%;
  }
}

/* 动画效果 */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.module-content {
  animation: fadeIn 0.3s ease-out;
}

.data-item,
.scenario-card,
.category-card,
.case-card,
.equipment-card,
.data-card,
.study-card,
.tool-category-card {
  animation: fadeIn 0.3s ease-out;
}

/* 工具类 */
.mt30 {
  margin-top: 30px;
}
</style>