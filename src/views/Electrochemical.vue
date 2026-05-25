<template>
  <Header></Header>
  <div class="process-data">
    <!-- 面包屑导航 -->
    <div class="mb-nav">
      <div class="container">
        <p>
          当前位置： <router-link to="/">首页</router-link> >
          <span>工艺数据</span>
        </p>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="container main-content">
      <div class="data-aggregation">
        <!-- 左侧导航栏 -->
        <div class="data-aggregation-left">
          <div class="left-sub-nav-box">
            <!-- 工艺数据库导航 -->
            <dl class="data-aggregation-nav"
                :class="{active: activeModule === 'overview'}"
                @click="switchModule('overview')">
              <dt class="index1">
                <a href="javascript:void(0)">工艺数据概览</a>
              </dt>
            </dl>

            <!-- 钢铁工艺模块 -->
            <dl class="data-aggregation-nav"
                :class="{active: activeModule === 'steel'}"
                @click="switchModule('steel')">
              <dt class="index2">
                <a href="javascript:void(0)">钢铁工艺流程</a>
                <p>
                  <i :style="{transform: (activeModule === 'steel' && isSteelMenuExpanded) ? 'rotate(180deg)' : 'rotate(0deg)'}"></i>
                </p>
              </dt>
              <dd :style="{display: (activeModule === 'steel' && isSteelMenuExpanded) ? 'block' : 'none'}">
                <ul class="data-aggregation-node">
                  <li v-for="item in steelProcessList"
                      :key="item.id"
                      :class="{active: activeSteelProcess === item.id}"
                      @click.stop="switchSteelProcess(item.id)">
                    <a href="javascript:void(0)">{{ item.name }}</a>
                  </li>
                </ul>
              </dd>
            </dl>

            <!-- 有色金属工艺 -->
            <dl class="data-aggregation-nav"
                :class="{active: activeModule === 'nonferrous'}"
                @click="switchModule('nonferrous')">
              <dt class="index3">
                <a href="javascript:void(0)">有色金属工艺</a>
              </dt>
            </dl>

            <!-- 化工工艺 -->
            <dl class="data-aggregation-nav"
                :class="{active: activeModule === 'chemical'}"
                @click="switchModule('chemical')">
              <dt class="index4">
                <a href="javascript:void(0)">化工工艺流程</a>
              </dt>
            </dl>

            <!-- 工艺优化 -->
            <dl class="data-aggregation-nav"
                :class="{active: activeModule === 'optimization'}"
                @click="switchModule('optimization')">
              <dt class="index5">
                <a href="javascript:void(0)">工艺优化案例</a>
              </dt>
            </dl>

            <!-- 工艺数据库统计 -->
            <dl class="data-aggregation-nav"
                :class="{active: activeModule === 'stats'}"
                @click="switchModule('stats')">
              <dt class="index6">
                <a href="javascript:void(0)">数据库统计</a>
              </dt>
            </dl>
          </div>
          <div class="m-nav-but">点击展开菜单</div>
        </div>

        <!-- 右侧内容展示区 -->
        <div class="data-aggregation-right">

          <!-- ==================== 工艺数据概览 ==================== -->
          <div class="module-content" v-if="activeModule === 'overview'">
            <div class="module-header">
              <h2><i class="fas fa-industry"></i> 工艺数据概览</h2>
              <p class="module-desc">全面的冶金工艺流程数据，覆盖钢铁、有色、化工等多个行业</p>
            </div>

            <!-- 关键指标 -->
            <div class="echarts-data-num">
              <div class="data-item">
                <dl>
                  <dt>工艺流程数</dt>
                  <dd>150+</dd>
                  <dd class="trend up">持续增加</dd>
                </dl>
                <div class="card-icon">
                  <i class="fas fa-project-diagram fa-2x"></i>
                </div>
              </div>

              <div class="data-item">
                <dl>
                  <dt>工艺参数记录</dt>
                  <dd>25,000+</dd>
                  <dd class="trend up">实时更新</dd>
                </dl>
                <div class="card-icon">
                  <i class="fas fa-database fa-2x"></i>
                </div>
              </div>

              <div class="data-item">
                <dl>
                  <dt>覆盖企业</dt>
                  <dd>3,200+</dd>
                  <dd class="trend up">同比 +15%</dd>
                </dl>
                <div class="card-icon">
                  <i class="fas fa-building fa-2x"></i>
                </div>
              </div>

              <div class="data-item">
                <dl>
                  <dt>优化案例</dt>
                  <dd>850+</dd>
                  <dd class="trend up">持续积累</dd>
                </dl>
                <div class="card-icon">
                  <i class="fas fa-chart-line fa-2x"></i>
                </div>
              </div>

              <div class="data-item">
                <dl>
                  <dt>节能效果</dt>
                  <dd>15-30%</dd>
                  <dd class="trend down">平均降低</dd>
                </dl>
                <div class="card-icon">
                  <i class="fas fa-leaf fa-2x"></i>
                </div>
              </div>

              <div class="data-item">
                <dl>
                  <dt>数据更新</dt>
                  <dd>2024-Q1</dd>
                  <dd class="trend down">最新版本</dd>
                </dl>
                <div class="card-icon">
                  <i class="fas fa-sync-alt fa-2x"></i>
                </div>
              </div>
            </div>

            <!-- 行业分布 -->
            <div class="industry-distribution mt30">
              <div class="section-header">
                <h3><i class="fas fa-chart-pie"></i> 工艺数据行业分布</h3>
                <p>各行业工艺数据占比情况</p>
              </div>
              <div class="distribution-chart">
                <div class="distribution-bars">
                  <div class="distribution-bar" style="width: 45%" title="钢铁行业: 45%">
                    <span class="bar-label">钢铁行业</span>
                    <span class="bar-value">45%</span>
                  </div>
                  <div class="distribution-bar" style="width: 25%; background-color: #00B4FF" title="有色金属: 25%">
                    <span class="bar-label">有色金属</span>
                    <span class="bar-value">25%</span>
                  </div>
                  <div class="distribution-bar" style="width: 20%; background-color: #4ECDC4" title="化工行业: 20%">
                    <span class="bar-label">化工行业</span>
                    <span class="bar-value">20%</span>
                  </div>
                  <div class="distribution-bar" style="width: 10%; background-color: #96CEB4" title="其他行业: 10%">
                    <span class="bar-label">其他行业</span>
                    <span class="bar-value">10%</span>
                  </div>
                </div>
                <div class="distribution-legend">
                  <div class="legend-item">
                    <span class="legend-color" style="background-color: #0046DB"></span>
                    <span class="legend-text">钢铁行业 (45%)</span>
                  </div>
                  <div class="legend-item">
                    <span class="legend-color" style="background-color: #00B4FF"></span>
                    <span class="legend-text">有色金属 (25%)</span>
                  </div>
                  <div class="legend-item">
                    <span class="legend-color" style="background-color: #4ECDC4"></span>
                    <span class="legend-text">化工行业 (20%)</span>
                  </div>
                  <div class="legend-item">
                    <span class="legend-color" style="background-color: #96CEB4"></span>
                    <span class="legend-text">其他行业 (10%)</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- ==================== 钢铁工艺流程 ==================== -->
          <div class="module-content" v-if="activeModule === 'steel'">
            <div class="module-header">
              <h2><i class="fas fa-industry"></i> {{ currentSteelProcess.name }}工艺流程</h2>
              <p class="module-desc">{{ currentSteelProcess.description }}</p>
            </div>

            <!-- 工艺关键指标 -->
            <div class="process-stats">
              <div class="stat-row">
                <div class="stat-box">
                  <div class="stat-icon">
                    <i class="fas fa-fire"></i>
                  </div>
                  <div class="stat-content">
                    <div class="stat-title">能耗指标</div>
                    <div class="stat-value">{{ currentSteelProcess.energyConsumption }}</div>
                    <div class="stat-change">标准煤当量</div>
                  </div>
                </div>

                <div class="stat-box">
                  <div class="stat-icon">
                    <i class="fas fa-clock"></i>
                  </div>
                  <div class="stat-content">
                    <div class="stat-title">生产周期</div>
                    <div class="stat-value">{{ currentSteelProcess.productionCycle }}</div>
                    <div class="stat-change">从原料到成品</div>
                  </div>
                </div>

                <div class="stat-box">
                  <div class="stat-icon">
                    <i class="fas fa-percentage"></i>
                  </div>
                  <div class="stat-content">
                    <div class="stat-title">成品率</div>
                    <div class="stat-value">{{ currentSteelProcess.yieldRate }}</div>
                    <div class="stat-change" :class="currentSteelProcess.yieldTrend > 0 ? 'up' : 'down'">
                      趋势 {{ currentSteelProcess.yieldTrend > 0 ? '+' : '' }}{{ currentSteelProcess.yieldTrend }}%
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 工艺流程图 -->
            <div class="process-flow">
              <div class="section-header">
                <h3><i class="fas fa-project-diagram"></i> 工艺流程图</h3>
                <p>{{ currentSteelProcess.name }}主要生产工序</p>
              </div>
              <div class="flow-diagram">
                <div class="flow-steps">
                  <div class="flow-step" v-for="(step, index) in currentSteelProcess.flowSteps" :key="index">
                    <div class="step-number">{{ index + 1 }}</div>
                    <div class="step-content">
                      <h4>{{ step.name }}</h4>
                      <p>{{ step.description }}</p>
                      <div class="step-meta">
                        <span><i class="fas fa-thermometer-half"></i> {{ step.temperature }}</span>
                        <span><i class="fas fa-clock"></i> {{ step.time }}</span>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 关键工艺参数 -->
            <div class="process-parameters">
              <div class="section-header">
                <h3><i class="fas fa-sliders-h"></i> 关键工艺参数</h3>
                <p>{{ currentSteelProcess.name }}核心控制参数</p>
              </div>
              <div class="parameters-table">
                <table>
                  <thead>
                  <tr>
                    <th>参数名称</th>
                    <th>控制范围</th>
                    <th>最优值</th>
                    <th>单位</th>
                    <th>影响指标</th>
                  </tr>
                  </thead>
                  <tbody>
                  <tr v-for="param in currentSteelProcess.parameters" :key="param.name">
                    <td>{{ param.name }}</td>
                    <td>{{ param.range }}</td>
                    <td class="optimal-value">{{ param.optimal }}</td>
                    <td>{{ param.unit }}</td>
                    <td>{{ param.impact }}</td>
                  </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- 节能潜力分析 -->
            <div class="energy-saving">
              <div class="section-header">
                <h3><i class="fas fa-leaf"></i> 节能潜力分析</h3>
                <p>{{ currentSteelProcess.name }}可实现的节能降耗措施</p>
              </div>
              <div class="saving-measures">
                <div class="measure-card" v-for="measure in currentSteelProcess.savingMeasures" :key="measure.id">
                  <div class="measure-icon">
                    <i :class="measure.icon"></i>
                  </div>
                  <div class="measure-content">
                    <h4>{{ measure.title }}</h4>
                    <p>{{ measure.description }}</p>
                    <div class="measure-effect">
                      <span class="saving-potential">
                        <i class="fas fa-bolt"></i> 节能潜力：{{ measure.potential }}
                      </span>
                      <span class="investment-cost">
                        <i class="fas fa-dollar-sign"></i> 投资回报期：{{ measure.payback }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- ==================== 有色金属工艺 ==================== -->
          <div class="module-content" v-if="activeModule === 'nonferrous'">
            <div class="module-header">
              <h2><i class="fas fa-atom"></i> 有色金属工艺流程</h2>
              <p class="module-desc">铝、铜、锌、铅等有色金属冶炼与加工工艺数据</p>
            </div>

            <!-- 工艺分类 -->
            <div class="process-categories">
              <div class="section-header">
                <h3><i class="fas fa-sitemap"></i> 工艺分类</h3>
              </div>
              <div class="categories-grid">
                <div class="category-card"
                     v-for="category in nonferrousCategories"
                     :key="category.id"
                     :class="{active: activeNonferrousCategory === category.id}"
                     @click="switchNonferrousCategory(category.id)">
                  <div class="category-icon">
                    <i :class="category.icon"></i>
                  </div>
                  <div class="category-content">
                    <h4>{{ category.name }}</h4>
                    <p>{{ category.description }}</p>
                    <div class="process-count">{{ category.count }}项工艺</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 工艺对比 -->
            <div class="process-comparison mt30">
              <div class="section-header">
                <h3><i class="fas fa-balance-scale"></i> 工艺技术对比</h3>
                <p>不同有色金属冶炼技术性能对比</p>
              </div>
              <div class="comparison-table">
                <table>
                  <thead>
                  <tr>
                    <th>工艺技术</th>
                    <th>能耗(标煤/t)</th>
                    <th>金属回收率</th>
                    <th>投资强度</th>
                    <th>环保水平</th>
                    <th>技术成熟度</th>
                  </tr>
                  </thead>
                  <tbody>
                  <tr v-for="tech in nonferrousTechnologies" :key="tech.id">
                    <td>{{ tech.name }}</td>
                    <td>{{ tech.energy }}</td>
                    <td>{{ tech.recovery }}</td>
                    <td>{{ tech.investment }}</td>
                    <td>
                      <div class="rating">
                        <i class="fas fa-star" v-for="n in tech.environment" :key="n"></i>
                      </div>
                    </td>
                    <td>{{ tech.maturity }}</td>
                  </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <!-- ==================== 化工工艺流程 ==================== -->
          <div class="module-content" v-if="activeModule === 'chemical'">
            <div class="module-header">
              <h2><i class="fas fa-flask"></i> 化工工艺流程</h2>
              <p class="module-desc">化肥、石化、精细化工等工艺流程与参数数据库</p>
            </div>

            <!-- 工艺查询 -->
            <div class="process-search">
              <div class="section-header">
                <h3><i class="fas fa-search"></i> 工艺数据查询</h3>
                <p>检索化工工艺流程与参数数据</p>
              </div>

              <div class="search-form">
                <div class="form-row">
                  <div class="form-group">
                    <label for="chemicalType"><i class="fas fa-vial"></i> 化工类型</label>
                    <select id="chemicalType" v-model="chemicalSearch.type">
                      <option value="">选择化工类型</option>
                      <option value="fertilizer">化肥工艺</option>
                      <option value="petrochemical">石油化工</option>
                      <option value="fine">精细化工</option>
                      <option value="basic">基础化工</option>
                    </select>
                  </div>

                  <div class="form-group">
                    <label for="processName"><i class="fas fa-cogs"></i> 工艺名称</label>
                    <input type="text" id="processName" v-model="chemicalSearch.name" placeholder="输入工艺名称">
                  </div>

                  <div class="form-group">
                    <label for="product"><i class="fas fa-box"></i> 主要产品</label>
                    <input type="text" id="product" v-model="chemicalSearch.product" placeholder="输入产品名称">
                  </div>
                </div>

                <div class="form-actions">
                  <button class="btn-search" @click="searchChemicalProcess">
                    <i class="fas fa-search"></i> 查询工艺
                  </button>
                  <button class="btn-reset" @click="resetChemicalSearch">
                    <i class="fas fa-redo"></i> 重置条件
                  </button>
                </div>
              </div>
            </div>

            <!-- 工艺数据展示 -->
            <div class="chemical-process-data mt30" v-if="chemicalResults.length > 0">
              <div class="results-header">
                <h3><i class="fas fa-table"></i> 工艺数据列表</h3>
                <div class="results-info">
                  <span>共找到 {{ chemicalResults.length }} 条记录</span>
                  <button class="btn-export" @click="exportChemicalData">
                    <i class="fas fa-download"></i> 导出数据
                  </button>
                </div>
              </div>

              <div class="chemical-results">
                <div class="chemical-card" v-for="process in chemicalResults" :key="process.id">
                  <div class="chemical-header">
                    <h4>{{ process.name }}</h4>
                    <span class="chemical-tag">{{ process.type }}</span>
                  </div>
                  <div class="chemical-content">
                    <div class="chemical-info">
                      <span><i class="fas fa-box"></i> 主要产品：{{ process.product }}</span>
                      <span><i class="fas fa-thermometer-half"></i> 反应温度：{{ process.temperature }}</span>
                      <span><i class="fas fa-tachometer-alt"></i> 压力：{{ process.pressure }}</span>
                    </div>
                    <p class="chemical-desc">{{ process.description }}</p>
                    <div class="chemical-metrics">
                      <div class="metric">
                        <i class="fas fa-bolt"></i>
                        <span>能耗：{{ process.energy }} tce/t</span>
                      </div>
                      <div class="metric">
                        <i class="fas fa-recycle"></i>
                        <span>原料转化率：{{ process.conversion }}%</span>
                      </div>
                      <div class="metric">
                        <i class="fas fa-leaf"></i>
                        <span>排放强度：{{ process.emission }} tCO₂/t</span>
                      </div>
                    </div>
                  </div>
                  <div class="chemical-footer">
                    <button class="btn-detail" @click="viewChemicalDetail(process)">
                      <i class="fas fa-info-circle"></i> 工艺详情
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- ==================== 工艺优化案例 ==================== -->
          <div class="module-content" v-if="activeModule === 'optimization'">
            <div class="module-header">
              <h2><i class="fas fa-chart-line"></i> 工艺优化案例库</h2>
              <p class="module-desc">实际工业应用的工艺优化案例，包含技术改造、节能降耗等</p>
            </div>

            <!-- 案例分类 -->
            <div class="case-categories">
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
            <div class="case-list">
              <div class="section-header">
                <h3><i class="fas fa-briefcase"></i> 优化案例列表</h3>
                <div class="list-controls">
                  <input type="text" placeholder="搜索案例..." v-model="caseSearch">
                  <select v-model="caseSort">
                    <option value="date">按时间</option>
                    <option value="effect">按效果</option>
                    <option value="industry">按行业</option>
                  </select>
                </div>
              </div>

              <div class="case-grid">
                <div class="case-card" v-for="caseItem in filteredCases" :key="caseItem.id">
                  <div class="case-header">
                    <h4>{{ caseItem.title }}</h4>
                    <span class="case-industry">{{ caseItem.industry }}</span>
                  </div>
                  <div class="case-content">
                    <div class="case-meta">
                      <span><i class="fas fa-building"></i> {{ caseItem.company }}</span>
                      <span><i class="fas fa-calendar"></i> {{ caseItem.date }}</span>
                      <span><i class="fas fa-tag"></i> {{ caseItem.type }}</span>
                    </div>
                    <p>{{ caseItem.description }}</p>
                    <div class="case-effects">
                      <div class="effect-item">
                        <i class="fas fa-bolt"></i>
                        <div>
                          <div class="effect-title">节能效果</div>
                          <div class="effect-value">{{ caseItem.energySaving }}</div>
                        </div>
                      </div>
                      <div class="effect-item">
                        <i class="fas fa-dollar-sign"></i>
                        <div>
                          <div class="effect-title">经济效益</div>
                          <div class="effect-value">{{ caseItem.economicBenefit }}</div>
                        </div>
                      </div>
                      <div class="effect-item">
                        <i class="fas fa-leaf"></i>
                        <div>
                          <div class="effect-title">减排效果</div>
                          <div class="effect-value">{{ caseItem.emissionReduction }}</div>
                        </div>
                      </div>
                    </div>
                  </div>
                  <div class="case-footer">
                    <button class="btn-detail" @click="viewCaseDetail(caseItem)">
                      <i class="fas fa-info-circle"></i> 查看详情
                    </button>
                    <button class="btn-download" @click="downloadCase(caseItem)">
                      <i class="fas fa-download"></i> 案例报告
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- ==================== 数据库统计 ==================== -->
          <div class="module-content" v-if="activeModule === 'stats'">
            <div class="module-header">
              <h2><i class="fas fa-chart-bar"></i> 工艺数据库统计</h2>
              <p class="module-desc">全面的工艺数据统计与分析</p>
            </div>

            <!-- 统计概览 -->
            <div class="stats-overview">
              <div class="stats-grid">
                <div class="stat-card">
                  <div class="stat-icon">
                    <i class="fas fa-database"></i>
                  </div>
                  <div class="stat-content">
                    <h4>数据总量</h4>
                    <div class="stat-number">28,500+</div>
                    <p>条工艺数据记录</p>
                    <div class="stat-change up">
                      <i class="fas fa-arrow-up"></i> 环比增长 +8.2%
                    </div>
                  </div>
                </div>

                <div class="stat-card">
                  <div class="stat-icon">
                    <i class="fas fa-industry"></i>
                  </div>
                  <div class="stat-content">
                    <h4>覆盖行业</h4>
                    <div class="stat-number">12+</div>
                    <p>个工业细分行业</p>
                    <div class="stat-change up">
                      <i class="fas fa-arrow-up"></i> 新增2个行业
                    </div>
                  </div>
                </div>

                <div class="stat-card">
                  <div class="stat-icon">
                    <i class="fas fa-cogs"></i>
                  </div>
                  <div class="stat-content">
                    <h4>工艺流程</h4>
                    <div class="stat-number">150+</div>
                    <p>套完整工艺流程</p>
                    <div class="stat-change up">
                      <i class="fas fa-arrow-up"></i> 新增15套工艺
                    </div>
                  </div>
                </div>

                <div class="stat-card">
                  <div class="stat-icon">
                    <i class="fas fa-chart-line"></i>
                  </div>
                  <div class="stat-content">
                    <h4>优化案例</h4>
                    <div class="stat-number">850+</div>
                    <p>个实际优化案例</p>
                    <div class="stat-change up">
                      <i class="fas fa-arrow-up"></i> 新增32个案例
                    </div>
                  </div>
                </div>

                <div class="stat-card">
                  <div class="stat-icon">
                    <i class="fas fa-building"></i>
                  </div>
                  <div class="stat-content">
                    <h4>合作企业</h4>
                    <div class="stat-number">3,200+</div>
                    <p>家工业企业</p>
                    <div class="stat-change up">
                      <i class="fas fa-arrow-up"></i> 同比增长 +15%
                    </div>
                  </div>
                </div>

                <div class="stat-card">
                  <div class="stat-icon">
                    <i class="fas fa-file-alt"></i>
                  </div>
                  <div class="stat-content">
                    <h4>工艺文档</h4>
                    <div class="stat-number">4,800+</div>
                    <p>份技术文档</p>
                    <div class="stat-change up">
                      <i class="fas fa-arrow-up"></i> 新增320份
                    </div>
                  </div>
                </div>

                <div class="stat-card">
                  <div class="stat-icon">
                    <i class="fas fa-chart-area"></i>
                  </div>
                  <div class="stat-content">
                    <h4>数据完整性</h4>
                    <div class="stat-number">95.2%</div>
                    <p>数据字段完整率</p>
                    <div class="stat-change up">
                      <i class="fas fa-arrow-up"></i> 提升2.1%
                    </div>
                  </div>
                </div>

                <div class="stat-card">
                  <div class="stat-icon">
                    <i class="fas fa-users"></i>
                  </div>
                  <div class="stat-content">
                    <h4>活跃用户</h4>
                    <div class="stat-number">5,600+</div>
                    <p>月活跃用户数</p>
                    <div class="stat-change up">
                      <i class="fas fa-arrow-up"></i> 增长28%
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 数据增长趋势 -->
            <div class="growth-trend mt30">
              <div class="section-header">
                <h3><i class="fas fa-chart-line"></i> 数据增长趋势</h3>
                <p>近12个月工艺数据增长情况</p>
              </div>
              <div class="trend-chart-container">
                <div class="trend-legend">
                  <div class="legend-item">
                    <span class="legend-dot" style="background-color: #0046DB"></span>
                    <span class="legend-text">新增数据记录</span>
                  </div>
                  <div class="legend-item">
                    <span class="legend-dot" style="background-color: #00B4FF"></span>
                    <span class="legend-text">新增工艺流程</span>
                  </div>
                </div>
                <div class="trend-bars">
                  <div class="trend-month" v-for="month in growthTrend" :key="month.month">
                    <div class="month-label">{{ month.month }}</div>
                    <div class="bar-container">
                      <div class="bar-data" :style="{height: month.dataHeight + '%'}"
                           :title="'新增数据：' + month.dataRecords + '条'">
                        <div class="bar-value">{{ month.dataRecords }}</div>
                      </div>
                      <div class="bar-process" :style="{height: month.processHeight + '%'}"
                           :title="'新增工艺：' + month.processCount + '套'">
                        <div class="bar-value">{{ month.processCount }}</div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 数据质量分析 -->
            <div class="data-quality mt30">
              <div class="section-header">
                <h3><i class="fas fa-check-circle"></i> 数据质量分析</h3>
                <p>工艺数据的准确性与完整性评估</p>
              </div>
              <div class="quality-metrics">
                <div class="quality-metric">
                  <div class="metric-header">
                    <span class="metric-title">数据准确度</span>
                    <span class="metric-value">98.5%</span>
                  </div>
                  <div class="metric-bar">
                    <div class="bar-fill" style="width: 98.5%"></div>
                  </div>
                  <div class="metric-footer">
                    <span class="metric-change up">
                      <i class="fas fa-arrow-up"></i> 提升0.8%
                    </span>
                    <span class="metric-desc">人工校验+算法验证</span>
                  </div>
                </div>

                <div class="quality-metric">
                  <div class="metric-header">
                    <span class="metric-title">数据完整性</span>
                    <span class="metric-value">95.2%</span>
                  </div>
                  <div class="metric-bar">
                    <div class="bar-fill" style="width: 95.2%"></div>
                  </div>
                  <div class="metric-footer">
                    <span class="metric-change up">
                      <i class="fas fa-arrow-up"></i> 提升2.1%
                    </span>
                    <span class="metric-desc">必填字段完成率</span>
                  </div>
                </div>

                <div class="quality-metric">
                  <div class="metric-header">
                    <span class="metric-title">数据时效性</span>
                    <span class="metric-value">96.8%</span>
                  </div>
                  <div class="metric-bar">
                    <div class="bar-fill" style="width: 96.8%"></div>
                  </div>
                  <div class="metric-footer">
                    <span class="metric-change up">
                      <i class="fas fa-arrow-up"></i> 提升1.5%
                    </span>
                    <span class="metric-desc">一年内更新数据占比</span>
                  </div>
                </div>

                <div class="quality-metric">
                  <div class="metric-header">
                    <span class="metric-title">数据一致性</span>
                    <span class="metric-value">97.1%</span>
                  </div>
                  <div class="metric-bar">
                    <div class="bar-fill" style="width: 97.1%"></div>
                  </div>
                  <div class="metric-footer">
                    <span class="metric-change up">
                      <i class="fas fa-arrow-up"></i> 提升1.2%
                    </span>
                    <span class="metric-desc">跨数据源一致性</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 热门工艺访问 -->
            <div class="popular-processes mt30">
              <div class="section-header">
                <h3><i class="fas fa-fire"></i> 热门工艺访问排行</h3>
                <p>近30天最受关注的工艺流程</p>
              </div>
              <div class="process-ranking">
                <div class="rank-list">
                  <div class="rank-item" v-for="(process, index) in popularProcesses" :key="process.id">
                    <div class="rank-index" :class="getRankClass(index)">
                      {{ index + 1 }}
                    </div>
                    <div class="rank-content">
                      <div class="rank-name">{{ process.name }}</div>
                      <div class="rank-industry">{{ process.industry }}</div>
                    </div>
                    <div class="rank-stats">
                      <div class="rank-views">
                        <i class="fas fa-eye"></i>
                        {{ process.views.toLocaleString() }}
                      </div>
                      <div class="rank-change" :class="process.change >= 0 ? 'up' : 'down'">
                        <i class="fas" :class="process.change >= 0 ? 'fa-arrow-up' : 'fa-arrow-down'"></i>
                        {{ Math.abs(process.change) }}%
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 数据来源分布 -->
            <div class="data-sources mt30">
              <div class="section-header">
                <h3><i class="fas fa-cloud-upload-alt"></i> 数据来源分布</h3>
                <p>工艺数据来源构成分析</p>
              </div>
              <div class="sources-chart">
                <div class="sources-visual">
                  <div class="donut-chart">
                    <div class="donut-segment" style="--percentage: 38; --color: #0046DB;"
                         title="企业上报：38%"></div>
                    <div class="donut-segment" style="--percentage: 25; --color: #00B4FF;"
                         title="行业监测：25%"></div>
                    <div class="donut-segment" style="--percentage: 22; --color: #4ECDC4;"
                         title="科研机构：22%"></div>
                    <div class="donut-segment" style="--percentage: 15; --color: #96CEB4;"
                         title="公开数据：15%"></div>
                    <div class="donut-center">
                      <div class="center-value">100%</div>
                      <div class="center-label">数据覆盖</div>
                    </div>
                  </div>
                </div>
                <div class="sources-legend">
                  <div class="legend-item" v-for="source in dataSources" :key="source.id">
                    <div class="legend-header">
                      <span class="legend-color" :style="{backgroundColor: source.color}"></span>
                      <span class="legend-text">{{ source.name }}</span>
                      <span class="legend-percentage">{{ source.percentage }}%</span>
                    </div>
                    <div class="legend-desc">{{ source.description }}</div>
                    <div class="legend-count">{{ source.count.toLocaleString() }} 条记录</div>
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
  name: "ProcessData",
  components: {
    Header,
    Footer,
  },
  data() {
    return {
      activeModule: 'overview',
      activeSteelProcess: 'blast_furnace',
      isSteelMenuExpanded: false,

      steelProcessList: [
        { id: 'blast_furnace', name: '高炉炼铁工艺' },
        { id: 'converter', name: '转炉炼钢工艺' },
        { id: 'electric_furnace', name: '电炉炼钢工艺' },
        { id: 'continuous_casting', name: '连铸工艺' },
        { id: 'hot_rolling', name: '热轧工艺' },
        { id: 'cold_rolling', name: '冷轧工艺' },
        { id: 'annealing', name: '退火工艺' },
        { id: 'coating', name: '涂镀工艺' }
      ],

      currentSteelProcess: {},

      // 有色金属工艺
      activeNonferrousCategory: 'all',
      nonferrousCategories: [
        { id: 'all', name: '全部工艺', icon: 'fas fa-boxes', description: '所有有色金属工艺', count: 45 },
        { id: 'aluminum', name: '铝冶炼', icon: 'fas fa-atom', description: '氧化铝、电解铝工艺', count: 12 },
        { id: 'copper', name: '铜冶炼', icon: 'fas fa-bolt', description: '火法、湿法炼铜', count: 10 },
        { id: 'zinc', name: '锌冶炼', icon: 'fas fa-industry', description: '湿法炼锌工艺', count: 8 },
        { id: 'lead', name: '铅冶炼', icon: 'fas fa-cogs', description: '铅冶炼与精炼', count: 7 },
        { id: 'rare', name: '稀有金属', icon: 'fas fa-gem', description: '稀土、钨钼等', count: 8 }
      ],

      nonferrousTechnologies: [
        { id: 1, name: '拜耳法氧化铝', energy: 450, recovery: 92, investment: '高', environment: 4, maturity: '成熟' },
        { id: 2, name: '预焙槽电解铝', energy: 13500, recovery: 96, investment: '很高', environment: 3, maturity: '成熟' },
        { id: 3, name: '闪速炼铜', energy: 280, recovery: 98, investment: '很高', environment: 4, maturity: '先进' },
        { id: 4, name: '湿法炼锌', energy: 1800, recovery: 95, investment: '中', environment: 4, maturity: '成熟' },
        { id: 5, name: '基夫赛特炼铅', energy: 320, recovery: 97, investment: '很高', environment: 5, maturity: '先进' }
      ],

      // 化工工艺搜索
      chemicalSearch: {
        type: '',
        name: '',
        product: ''
      },
      chemicalResults: [],

      // 优化案例
      activeCaseCategory: 'all',
      caseSearch: '',
      caseSort: 'date',
      caseCategories: [
        { id: 'all', name: '全部案例', count: 850 },
        { id: 'energy', name: '节能改造', count: 320 },
        { id: 'process', name: '工艺优化', count: 280 },
        { id: 'equipment', name: '设备更新', count: 150 },
        { id: 'automation', name: '自动化', count: 100 }
      ],

      // 数据库统计 - 新增数据
      growthTrend: [
        { month: '1月', dataRecords: 1850, processCount: 8, dataHeight: 65, processHeight: 40 },
        { month: '2月', dataRecords: 2100, processCount: 10, dataHeight: 75, processHeight: 50 },
        { month: '3月', dataRecords: 2450, processCount: 12, dataHeight: 85, processHeight: 60 },
        { month: '4月', dataRecords: 2300, processCount: 11, dataHeight: 80, processHeight: 55 },
        { month: '5月', dataRecords: 2650, processCount: 14, dataHeight: 92, processHeight: 70 },
        { month: '6月', dataRecords: 2800, processCount: 15, dataHeight: 98, processHeight: 75 },
        { month: '7月', dataRecords: 2950, processCount: 16, dataHeight: 100, processHeight: 80 },
        { month: '8月', dataRecords: 3100, processCount: 18, dataHeight: 108, processHeight: 90 },
        { month: '9月', dataRecords: 2850, processCount: 17, dataHeight: 100, processHeight: 85 },
        { month: '10月', dataRecords: 3200, processCount: 20, dataHeight: 112, processHeight: 100 },
        { month: '11月', dataRecords: 3350, processCount: 22, dataHeight: 118, processHeight: 110 },
        { month: '12月', dataRecords: 3500, processCount: 25, dataHeight: 122, processHeight: 125 }
      ],

      popularProcesses: [
        { id: 1, name: '高炉炼铁工艺', industry: '钢铁', views: 12560, change: 12.5 },
        { id: 2, name: '电解铝工艺', industry: '有色金属', views: 9870, change: 8.3 },
        { id: 3, name: '合成氨工艺', industry: '化工', views: 8450, change: 15.2 },
        { id: 4, name: '转炉炼钢工艺', industry: '钢铁', views: 7320, change: 5.8 },
        { id: 5, name: '乙烯裂解工艺', industry: '石化', views: 6890, change: 9.7 },
        { id: 6, name: '铜火法冶炼', industry: '有色金属', views: 6540, change: 7.2 },
        { id: 7, name: '连铸工艺', industry: '钢铁', views: 5890, change: 11.4 },
        { id: 8, name: '尿素合成工艺', industry: '化肥', views: 5230, change: 6.9 },
        { id: 9, name: '热轧工艺', industry: '钢铁', views: 4870, change: 4.5 },
        { id: 10, name: '甲醇合成工艺', industry: '化工', views: 4320, change: 13.1 }
      ],

      dataSources: [
        { id: 1, name: '企业上报', percentage: 38, color: '#0046DB', description: '合作企业生产数据上报', count: 10830 },
        { id: 2, name: '行业监测', percentage: 25, color: '#00B4FF', description: '行业协会监测数据', count: 7125 },
        { id: 3, name: '科研机构', percentage: 22, color: '#4ECDC4', description: '大学及研究院数据', count: 6270 },
        { id: 4, name: '公开数据', percentage: 15, color: '#96CEB4', description: '政府公开及文献数据', count: 4275 }
      ]
    };
  },
  computed: {
    filteredCases() {
      // 模拟数据过滤
      return [
        {
          id: 1,
          title: '高炉煤气余压发电改造',
          industry: '钢铁',
          company: '某钢铁集团',
          date: '2023-06',
          type: '节能改造',
          description: '采用TRT技术回收高炉煤气余压发电，年发电量增加15%',
          energySaving: '12,000 tce/年',
          economicBenefit: '800万元/年',
          emissionReduction: '30,000 tCO₂/年'
        },
        {
          id: 2,
          title: '转炉煤气回收系统优化',
          industry: '钢铁',
          company: '某钢铁公司',
          date: '2023-08',
          type: '工艺优化',
          description: '优化转炉煤气回收系统，提高煤气回收率',
          energySaving: '8,500 tce/年',
          economicBenefit: '550万元/年',
          emissionReduction: '21,000 tCO₂/年'
        },
        {
          id: 3,
          title: '铝电解槽节能改造',
          industry: '有色金属',
          company: '某铝业公司',
          date: '2023-10',
          type: '节能改造',
          description: '优化电解槽结构，降低电解能耗',
          energySaving: '15,000 tce/年',
          economicBenefit: '1,200万元/年',
          emissionReduction: '38,000 tCO₂/年'
        },
        {
          id: 4,
          title: '化工反应器自动化控制',
          industry: '化工',
          company: '某化工企业',
          date: '2023-12',
          type: '自动化',
          description: '实现反应过程自动化控制，提高反应效率',
          energySaving: '3,200 tce/年',
          economicBenefit: '280万元/年',
          emissionReduction: '8,000 tCO₂/年'
        }
      ];
    }
  },
  created() {
    this.switchSteelProcess('blast_furnace');
    this.searchChemicalProcess();
  },
  methods: {
    switchModule(module) {
      if (module === 'steel') {
        if (this.activeModule === 'steel') {
          this.isSteelMenuExpanded = !this.isSteelMenuExpanded;
        } else {
          this.activeModule = module;
          this.isSteelMenuExpanded = false;
          this.switchSteelProcess('blast_furnace');
        }
      } else {
        this.activeModule = module;
        this.isSteelMenuExpanded = false;
      }
    },

    switchSteelProcess(processId) {
      this.activeSteelProcess = processId;
      this.isSteelMenuExpanded = true;

      const processData = {
        blast_furnace: {
          name: '高炉炼铁工艺',
          description: '高炉炼铁是现代钢铁生产的主要工艺，将铁矿石还原为生铁。该工艺能耗高，是钢铁企业节能减排的重点。',
          energyConsumption: '380-450 kgce/t',
          productionCycle: '6-8小时',
          yieldRate: '98.5%',
          yieldTrend: 0.5,
          flowSteps: [
            { name: '原料准备', description: '铁矿石、焦炭、熔剂等原料的破碎、筛分、混匀', temperature: '常温', time: '1-2小时' },
            { name: '高炉炼铁', description: '原料从炉顶装入，热风从风口鼓入，进行还原反应', temperature: '1450-1550°C', time: '4-6小时' },
            { name: '铁水处理', description: '铁水从出铁口放出，进行脱硫、扒渣等处理', temperature: '1350-1450°C', time: '30-60分钟' },
            { name: '炉渣处理', description: '炉渣水淬处理，回收余热，生产水渣产品', temperature: '1400-1500°C', time: '连续' }
          ],
          parameters: [
            { name: '风温', range: '1150-1250°C', optimal: '1200°C', unit: '°C', impact: '焦比、产量' },
            { name: '富氧率', range: '2-5%', optimal: '3.5%', unit: '%', impact: '燃烧效率、产量' },
            { name: '顶压', range: '200-250 kPa', optimal: '220 kPa', unit: 'kPa', impact: '煤气分布、顺行' },
            { name: '燃料比', range: '480-520 kg/t', optimal: '500 kg/t', unit: 'kg/t', impact: '能耗、成本' },
            { name: '炉温', range: '1450-1550°C', optimal: '1500°C', unit: '°C', impact: '铁水质量、炉况' }
          ],
          savingMeasures: [
            {
              id: 1,
              title: '高炉煤气余压发电(TRT)',
              description: '利用高炉煤气压力能发电，提高能源利用效率',
              potential: '25-30 kWh/t',
              payback: '2-3年',
              icon: 'fas fa-bolt'
            },
            {
              id: 2,
              title: '热风炉废气余热回收',
              description: '回收热风炉废气余热，预热助燃空气和煤气',
              potential: '8-12 kgce/t',
              payback: '1-2年',
              icon: 'fas fa-fire'
            },
            {
              id: 3,
              title: '高炉喷吹煤粉',
              description: '喷吹煤粉替代部分焦炭，降低燃料成本',
              potential: '15-20 kgce/t',
              payback: '6-12个月',
              icon: 'fas fa-industry'
            },
            {
              id: 4,
              title: '智能燃烧控制',
              description: '采用智能控制系统优化燃烧过程',
              potential: '3-5%燃料节约',
              payback: '1年',
              icon: 'fas fa-brain'
            }
          ]
        },
        converter: {
          name: '转炉炼钢工艺',
          description: '转炉炼钢是以铁水为主要原料的炼钢方法，通过吹氧降碳，生产合格钢水。',
          energyConsumption: '-15-0 kgce/t',
          productionCycle: '30-40分钟',
          yieldRate: '99.0%',
          yieldTrend: 0.3,
          flowSteps: [
            { name: '铁水预处理', description: '铁水脱硫、脱硅、脱磷处理', temperature: '1300-1350°C', time: '15-20分钟' },
            { name: '转炉吹炼', description: '顶底复吹，脱碳、升温、脱磷', temperature: '1600-1650°C', time: '15-20分钟' },
            { name: '出钢', description: '钢水倒入钢包，进行合金化', temperature: '1620-1650°C', time: '3-5分钟' },
            { name: '炉渣处理', description: '炉渣改质处理，回收含铁资源', temperature: '1550-1600°C', time: '连续' }
          ],
          parameters: [
            { name: '吹氧时间', range: '14-18分钟', optimal: '16分钟', unit: '分钟', impact: '脱碳效率、终点控制' },
            { name: '终点碳', range: '0.03-0.08%', optimal: '0.05%', unit: '%', impact: '钢水质量、合金消耗' },
            { name: '终点温度', range: '1620-1650°C', optimal: '1635°C', unit: '°C', impact: '浇铸温度、炉衬寿命' },
            { name: '供氧强度', range: '3.0-3.5 Nm³/t·min', optimal: '3.2 Nm³/t·min', unit: 'Nm³/t·min', impact: '反应速度、喷溅' },
            { name: '底吹流量', range: '0.03-0.06 Nm³/t·min', optimal: '0.045 Nm³/t·min', unit: 'Nm³/t·min', impact: '搅拌效果、终点控制' }
          ],
          savingMeasures: [
            {
              id: 1,
              title: '转炉煤气回收',
              description: '回收转炉煤气用于发电或燃料',
              potential: '80-100 m³/t',
              payback: '1-2年',
              icon: 'fas fa-recycle'
            },
            {
              id: 2,
              title: '钢包烘烤节能',
              description: '优化钢包烘烤工艺，减少煤气消耗',
              potential: '2-3 m³煤气/t',
              payback: '6个月',
              icon: 'fas fa-fire'
            },
            {
              id: 3,
              title: '智能炼钢',
              description: '采用人工智能优化炼钢过程',
              potential: '3-5 kgce/t',
              payback: '1年',
              icon: 'fas fa-robot'
            },
            {
              id: 4,
              title: '少渣炼钢',
              description: '优化造渣工艺，减少石灰消耗',
              potential: '10-15 kg石灰/t',
              payback: '立即见效',
              icon: 'fas fa-leaf'
            }
          ]
        },
        electric_furnace: {
          name: '电炉炼钢工艺',
          description: '电炉炼钢以废钢为主要原料，利用电能熔化废钢并精炼成钢水，适合短流程炼钢。',
          energyConsumption: '350-420 kWh/t',
          productionCycle: '50-70分钟',
          yieldRate: '97.5%',
          yieldTrend: 0.4,
          flowSteps: [
            { name: '废钢配料', description: '废钢分类、称重、配料，控制有害元素含量', temperature: '常温', time: '10-15分钟' },
            { name: '炉料熔化', description: '电极通电产生电弧，熔化废钢和合金料', temperature: '1550-1650°C', time: '25-35分钟' },
            { name: '氧化期', description: '吹氧脱碳、脱磷，去除钢中杂质', temperature: '1600-1700°C', time: '10-15分钟' },
            { name: '还原期', description: '脱氧、脱硫，调整合金成分', temperature: '1580-1620°C', time: '5-10分钟' }
          ],
          parameters: [
            { name: '电弧功率', range: '50-80 MW', optimal: '65 MW', unit: 'MW', impact: '熔化速度、能耗' },
            { name: '电极消耗', range: '1.5-2.5 kg/t', optimal: '1.8 kg/t', unit: 'kg/t', impact: '生产成本' },
            { name: '供氧强度', range: '25-35 Nm³/t·h', optimal: '30 Nm³/t·h', unit: 'Nm³/t·h', impact: '脱碳效率、冶炼时间' },
            { name: '泡沫渣厚度', range: '200-400 mm', optimal: '300 mm', unit: 'mm', impact: '电弧稳定、热效率' },
            { name: '终点碳', range: '0.05-0.15%', optimal: '0.10%', unit: '%', impact: '钢水质量、合金收得率' }
          ],
          savingMeasures: [
            {
              id: 1,
              title: '废钢预热',
              description: '利用烟气余热预热废钢，降低电耗',
              potential: '30-50 kWh/t',
              payback: '2-3年',
              icon: 'fas fa-fire'
            },
            {
              id: 2,
              title: '智能供电',
              description: '优化供电曲线，提高电能利用效率',
              potential: '20-30 kWh/t',
              payback: '1年',
              icon: 'fas fa-bolt'
            },
            {
              id: 3,
              title: '烟气余热回收',
              description: '回收电炉高温烟气产生蒸汽或发电',
              potential: '40-60 kWh/t',
              payback: '2-3年',
              icon: 'fas fa-recycle'
            },
            {
              id: 4,
              title: '氧燃助熔',
              description: '采用氧燃烧嘴辅助熔化，缩短冶炼时间',
              potential: '15-25 kWh/t',
              payback: '1-2年',
              icon: 'fas fa-burn'
            }
          ]
        },
        continuous_casting: {
          name: '连铸工艺',
          description: '将钢水连续浇铸成钢坯的工艺，取代模铸，提高生产效率和金属收得率。',
          energyConsumption: '15-25 kgce/t',
          productionCycle: '连续',
          yieldRate: '99.2%',
          yieldTrend: 0.2,
          flowSteps: [
            { name: '钢包准备', description: '钢水镇静、温度调整、吹氩处理', temperature: '1550-1580°C', time: '20-30分钟' },
            { name: '中间包烘烤', description: '预热中间包，防止钢水降温过快', temperature: '1100-1200°C', time: '2-3小时' },
            { name: '结晶器浇铸', description: '钢水注入结晶器，形成凝固壳', temperature: '1520-1550°C', time: '连续' },
            { name: '二冷区冷却', description: '喷水冷却，控制铸坯凝固', temperature: '800-1200°C', time: '连续' },
            { name: '切割成坯', description: '将连续铸坯切割成定尺长度', temperature: '700-900°C', time: '连续' }
          ],
          parameters: [
            { name: '拉坯速度', range: '0.8-1.8 m/min', optimal: '1.2 m/min', unit: 'm/min', impact: '产量、表面质量' },
            { name: '过热度', range: '15-35°C', optimal: '25°C', unit: '°C', impact: '铸坯质量、拉速' },
            { name: '二冷水量', range: '1.0-2.0 L/kg', optimal: '1.5 L/kg', unit: 'L/kg', impact: '凝固组织、裂纹' },
            { name: '结晶器振幅', range: '3-8 mm', optimal: '5 mm', unit: 'mm', impact: '润滑、表面质量' },
            { name: '结晶器锥度', range: '0.8-1.2%', optimal: '1.0%', unit: '%/m', impact: '气隙、传热' }
          ],
          savingMeasures: [
            {
              id: 1,
              title: '结晶器电磁搅拌',
              description: '改善铸坯内部质量，减少中心偏析',
              potential: '提高合格率2-3%',
              payback: '2-3年',
              icon: 'fas fa-magnet'
            },
            {
              id: 2,
              title: '二冷动态控制',
              description: '根据钢种和拉速动态调整冷却水量',
              potential: '减少裂纹缺陷30%',
              payback: '1-2年',
              icon: 'fas fa-tint'
            },
            {
              id: 3,
              title: '中间包保温',
              description: '优化中间包保温措施，减少温降',
              potential: '节能5-8 kgce/t',
              payback: '6-12个月',
              icon: 'fas fa-temperature-high'
            },
            {
              id: 4,
              title: '铸坯热装热送',
              description: '高温铸坯直接送轧钢工序',
              potential: '节能30-50 kgce/t',
              payback: '1-2年',
              icon: 'fas fa-fire-alt'
            }
          ]
        },
        hot_rolling: {
          name: '热轧工艺',
          description: '将钢坯加热后通过轧机轧制成所需规格的热轧产品的工艺。',
          energyConsumption: '50-80 kgce/t',
          productionCycle: '2-4小时',
          yieldRate: '98.0%',
          yieldTrend: 0.3,
          flowSteps: [
            { name: '板坯加热', description: '板坯在加热炉中加热至轧制温度', temperature: '1150-1250°C', time: '2-3小时' },
            { name: '高压水除鳞', description: '清除板坯表面氧化铁皮', temperature: '1100-1200°C', time: '1-2分钟' },
            { name: '粗轧', description: '多道次轧制，减小厚度', temperature: '1000-1100°C', time: '10-15分钟' },
            { name: '精轧', description: '精确控制成品尺寸和板形', temperature: '850-950°C', time: '5-10分钟' },
            { name: '层流冷却', description: '控制冷却速度，获得所需组织性能', temperature: '500-700°C', time: '1-2分钟' }
          ],
          parameters: [
            { name: '终轧温度', range: '820-900°C', optimal: '860°C', unit: '°C', impact: '力学性能、晶粒度' },
            { name: '卷取温度', range: '550-650°C', optimal: '600°C', unit: '°C', impact: '组织性能、表面质量' },
            { name: '轧制力', range: '20-40 MN', optimal: '30 MN', unit: 'MN', impact: '厚度精度、轧辊磨损' },
            { name: '轧制速度', range: '8-18 m/s', optimal: '12 m/s', unit: 'm/s', impact: '产量、温度控制' },
            { name: '压下率', range: '30-50%', optimal: '40%', unit: '%', impact: '变形量、能耗' }
          ],
          savingMeasures: [
            {
              id: 1,
              title: '加热炉富氧燃烧',
              description: '提高燃烧效率，降低燃料消耗',
              potential: '8-12 kgce/t',
              payback: '1-2年',
              icon: 'fas fa-fire'
            },
            {
              id: 2,
              title: '热轧润滑',
              description: '轧制过程润滑，降低轧制力和能耗',
              potential: '5-8%能耗降低',
              payback: '1年',
              icon: 'fas fa-oil-can'
            },
            {
              id: 3,
              title: '轧机主传动变频',
              description: '变频调速，提高电能利用效率',
              potential: '15-20%节电',
              payback: '2-3年',
              icon: 'fas fa-cogs'
            },
            {
              id: 4,
              title: '余热回收发电',
              description: '回收加热炉烟气余热发电',
              potential: '10-15 kWh/t',
              payback: '3-4年',
              icon: 'fas fa-bolt'
            }
          ]
        },
        cold_rolling: {
          name: '冷轧工艺',
          description: '在室温下对热轧板进行轧制，获得高精度、良好表面质量的冷轧产品。',
          energyConsumption: '80-120 kWh/t',
          productionCycle: '3-5天',
          yieldRate: '96.5%',
          yieldTrend: 0.4,
          flowSteps: [
            { name: '酸洗', description: '去除热轧板表面氧化铁皮', temperature: '60-80°C', time: '1-2分钟' },
            { name: '冷轧', description: '多机架连轧，大变形量轧制', temperature: '室温', time: '连续' },
            { name: '退火', description: '再结晶退火，消除加工硬化', temperature: '650-750°C', time: '10-20小时' },
            { name: '平整', description: '改善板形和表面质量', temperature: '室温', time: '连续' },
            { name: '精整', description: '剪切、分卷、包装', temperature: '室温', time: '1-2小时' }
          ],
          parameters: [
            { name: '轧制力', range: '15-25 MN', optimal: '20 MN', unit: 'MN', impact: '厚度精度、板形' },
            { name: '轧制速度', range: '15-25 m/s', optimal: '20 m/s', unit: 'm/s', impact: '产量、表面质量' },
            { name: '压下率', range: '50-80%', optimal: '65%', unit: '%', impact: '变形量、能耗' },
            { name: '张力', range: '50-150 kN', optimal: '100 kN', unit: 'kN', impact: '板形控制、稳定轧制' },
            { name: '轧辊粗糙度', range: '0.5-2.0 μm', optimal: '1.2 μm', unit: 'μm', impact: '表面质量、摩擦系数' }
          ],
          savingMeasures: [
            {
              id: 1,
              title: '高效酸洗',
              description: '优化酸洗工艺，降低酸耗和水耗',
              potential: '降低酸耗20-30%',
              payback: '1年',
              icon: 'fas fa-flask'
            },
            {
              id: 2,
              title: '退炉余热回收',
              description: '回收退火炉废气余热预热助燃空气',
              potential: '8-12%燃料节约',
              payback: '1-2年',
              icon: 'fas fa-fire'
            },
            {
              id: 3,
              title: '轧制油回收',
              description: '轧制油循环使用，降低消耗',
              potential: '降低油耗40-50%',
              payback: '1年',
              icon: 'fas fa-recycle'
            },
            {
              id: 4,
              title: '变频传动系统',
              description: '主传动和辅助传动采用变频控制',
              potential: '节电15-20%',
              payback: '2-3年',
              icon: 'fas fa-cogs'
            }
          ]
        },
        annealing: {
          name: '退火工艺',
          description: '通过加热和缓慢冷却，消除冷加工硬化，改善材料的组织和性能。',
          energyConsumption: '40-60 kgce/t',
          productionCycle: '10-30小时',
          yieldRate: '99.8%',
          yieldTrend: 0.1,
          flowSteps: [
            { name: '装炉', description: '钢材装入退火炉，合理摆放保证受热均匀', temperature: '室温', time: '1-2小时' },
            { name: '加热', description: '缓慢升温至退火温度，防止变形和开裂', temperature: '600-750°C', time: '4-8小时' },
            { name: '保温', description: '在退火温度下保持一定时间，完成组织转变', temperature: '650-750°C', time: '4-10小时' },
            { name: '冷却', description: '控制冷却速度，获得所需组织和性能', temperature: '650°C→室温', time: '8-16小时' },
            { name: '出炉', description: '冷却至安全温度后出炉', temperature: '≤100°C', time: '1-2小时' }
          ],
          parameters: [
            { name: '退火温度', range: '650-750°C', optimal: '700°C', unit: '°C', impact: '再结晶程度、硬度' },
            { name: '保温时间', range: '2-10小时', optimal: '6小时', unit: '小时', impact: '组织均匀性、性能' },
            { name: '加热速度', range: '50-150°C/h', optimal: '100°C/h', unit: '°C/h', impact: '变形、表面质量' },
            { name: '冷却速度', range: '20-50°C/h', optimal: '30°C/h', unit: '°C/h', impact: '组织、力学性能' },
            { name: '炉内气氛', range: '氮氢混合', optimal: '95%N₂+5%H₂', unit: '-', impact: '表面氧化、脱碳' }
          ],
          savingMeasures: [
            {
              id: 1,
              title: '蓄热式燃烧',
              description: '采用蓄热式燃烧技术，提高热效率',
              potential: '节能30-40%',
              payback: '2-3年',
              icon: 'fas fa-fire'
            },
            {
              id: 2,
              title: '炉体保温优化',
              description: '采用高效保温材料，减少散热损失',
              potential: '节能15-20%',
              payback: '1-2年',
              icon: 'fas fa-temperature-high'
            },
            {
              id: 3,
              title: '智能温控系统',
              description: '根据产品规格自动优化退火曲线',
              potential: '节能8-12%',
              payback: '1年',
              icon: 'fas fa-brain'
            },
            {
              id: 4,
              title: '废气余热利用',
              description: '回收废气余热预热入炉冷料',
              potential: '节能10-15%',
              payback: '2年',
              icon: 'fas fa-recycle'
            }
          ]
        },
        coating: {
          name: '涂镀工艺',
          description: '在钢材表面涂覆金属或非金属涂层，提高耐腐蚀性、装饰性或特殊功能。',
          energyConsumption: '30-50 kgce/t',
          productionCycle: '1-3分钟',
          yieldRate: '98.5%',
          yieldTrend: 0.2,
          flowSteps: [
            { name: '表面处理', description: '脱脂、清洗、磷化等前处理工序', temperature: '40-70°C', time: '30-60秒' },
            { name: '涂层制备', description: '调配涂料，控制粘度、固含量等参数', temperature: '20-30°C', time: '连续' },
            { name: '涂覆', description: '采用辊涂、喷涂等方式均匀涂覆', temperature: '20-40°C', time: '10-30秒' },
            { name: '固化', description: '加热使涂层干燥固化', temperature: '200-300°C', time: '30-60秒' },
            { name: '冷却', description: '冷却至室温，检查涂层质量', temperature: '300°C→室温', time: '30-60秒' }
          ],
          parameters: [
            { name: '涂层厚度', range: '10-30 μm', optimal: '20 μm', unit: 'μm', impact: '耐腐蚀性、成本' },
            { name: '固化温度', range: '200-300°C', optimal: '250°C', unit: '°C', impact: '涂层性能、能耗' },
            { name: '固化时间', range: '20-60秒', optimal: '40秒', unit: '秒', impact: '固化程度、产能' },
            { name: '涂层粘度', range: '30-80 s', optimal: '50 s', unit: '涂-4杯秒', impact: '涂层均匀性、厚度' },
            { name: '生产线速度', range: '60-150 m/min', optimal: '100 m/min', unit: 'm/min', impact: '产量、涂层质量' }
          ],
          savingMeasures: [
            {
              id: 1,
              title: '高效固化技术',
              description: '采用红外、UV等高效固化方式',
              potential: '节能30-40%',
              payback: '2-3年',
              icon: 'fas fa-sun'
            },
            {
              id: 2,
              title: '废气焚烧余热回收',
              description: '有机废气焚烧后回收热能',
              potential: '节能20-30%',
              payback: '2年',
              icon: 'fas fa-recycle'
            },
            {
              id: 3,
              title: '涂料循环利用',
              description: '回收利用过喷涂料，降低消耗',
              potential: '降低涂料消耗15-20%',
              payback: '1年',
              icon: 'fas fa-recycle'
            },
            {
              id: 4,
              title: '热风循环利用',
              description: '固化炉热风循环利用，减少热量损失',
              potential: '节能15-20%',
              payback: '1-2年',
              icon: 'fas fa-wind'
            }
          ]
        }
      };

      this.currentSteelProcess = processData[processId] || processData.blast_furnace;
    },

    switchNonferrousCategory(categoryId) {
      this.activeNonferrousCategory = categoryId;
    },

    searchChemicalProcess() {
      this.chemicalResults = [
        {
          id: 1,
          name: '合成氨工艺',
          type: '化肥工艺',
          product: '氨(NH₃)',
          temperature: '400-500°C',
          pressure: '15-30 MPa',
          description: '哈伯-博世法合成氨，氮气和氢气在高温高压下反应生成氨',
          energy: '1.2-1.5 tce/t',
          conversion: '25-30%',
          emission: '2.8-3.2 tCO₂/t'
        },
        {
          id: 2,
          name: '乙烯裂解工艺',
          type: '石油化工',
          product: '乙烯(C₂H₄)',
          temperature: '750-850°C',
          pressure: '0.1-0.3 MPa',
          description: '石脑油或轻烃蒸汽裂解生产乙烯，副产丙烯、丁二烯等',
          energy: '0.5-0.7 tce/t',
          conversion: '30-35%',
          emission: '1.5-1.8 tCO₂/t'
        },
        {
          id: 3,
          name: '甲醇合成工艺',
          type: '基础化工',
          product: '甲醇(CH₃OH)',
          temperature: '220-280°C',
          pressure: '5-10 MPa',
          description: '合成气(CO+H₂)在催化剂作用下合成甲醇',
          energy: '1.0-1.3 tce/t',
          conversion: '95-98%',
          emission: '2.0-2.5 tCO₂/t'
        },
        {
          id: 4,
          name: '聚氯乙烯工艺',
          type: '精细化工',
          product: 'PVC',
          temperature: '50-70°C',
          pressure: '0.5-1.0 MPa',
          description: '氯乙烯单体聚合生产聚氯乙烯树脂',
          energy: '0.8-1.0 tce/t',
          conversion: '85-90%',
          emission: '1.8-2.2 tCO₂/t'
        }
      ];
    },

    resetChemicalSearch() {
      this.chemicalSearch = {
        type: '',
        name: '',
        product: ''
      };
      this.chemicalResults = [];
    },

    switchCaseCategory(categoryId) {
      this.activeCaseCategory = categoryId;
    },

    exportChemicalData() {
      alert('化工工艺数据导出功能开发中...');
    },

    viewChemicalDetail(process) {
      alert(`查看工艺详情：\n工艺名称：${process.name}\n产品：${process.product}\n能耗：${process.energy} tce/t\n转化率：${process.conversion}%`);
    },

    viewCaseDetail(caseItem) {
      alert(`查看案例详情：\n${caseItem.title}\n企业：${caseItem.company}\n节能效果：${caseItem.energySaving}\n经济效益：${caseItem.economicBenefit}`);
    },

    downloadCase(caseItem) {
      alert(`下载案例报告：${caseItem.title}\n报告正在生成中...`);
    },

    getRankClass(index) {
      if (index === 0) return 'rank-gold';
      if (index === 1) return 'rank-silver';
      if (index === 2) return 'rank-bronze';
      return '';
    }
  }
};
</script>

<style scoped>
/* ==================== 基础样式 ==================== */
.process-data {
  background-color: #f5f7fa;
  min-height: 120vh;
  font-family: 'Microsoft YaHei', 'Segoe UI', Arial, sans-serif;
  display: flex;
  flex-direction: column;
  padding-top: 80px;
}

/* 容器 */
.container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 15px;
}

/* 主内容区域 - 调整顶部间距 */
.main-content {
  padding: 10px 0 30px;
  flex: 1;
}

/* ==================== 核心修改：使用 CSS Grid 实现左右栏一致 ==================== */
.data-aggregation {
  display: grid;
  grid-template-columns: 220px 1fr;
  gap: 24px;
  align-items: stretch;
}

/* ==================== 左侧导航栏样式 ==================== */
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

.data-aggregation-nav dt p {
  height: 100%;
  width: 54px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.data-aggregation-nav dt p i {
  display: block;
  width: 0;
  height: 0;
  border-left: 5px solid transparent;
  border-right: 5px solid transparent;
  border-top: 7px solid #999;
  transition: transform 0.3s;
  transform: rotate(0deg);
}

.data-aggregation-nav dt.active p i {
  border-top-color: #0046DB;
  transform: rotate(180deg);
}

.data-aggregation-nav dd {
  display: none;
  background: #F7F9FB;
  padding: 10px 0;
  border-top: 1px solid #e8e8e8;
}

.data-aggregation-node {
  width: 100%;
  list-style: none;
  padding: 0;
  margin: 0;
}

.data-aggregation-node li {
  width: 100%;
  border-bottom: 1px solid #e5e5e5;
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  cursor: pointer;
  transition: background-color 0.3s;
}

.data-aggregation-node li:hover {
  background-color: #edf2f7;
}

.data-aggregation-node li.active {
  background-color: #e6f7ff;
}

.data-aggregation-node li:last-child {
  border: none;
}

.data-aggregation-node li > a {
  color: #333;
  text-decoration: none;
  width: 100%;
  height: 44px;
  display: flex;
  align-items: center;
  padding-left: 40px;
  font-size: 14px;
  transition: color 0.3s;
}

.data-aggregation-node li:hover > a {
  color: #0046DB;
}

.data-aggregation-node li.active > a {
  color: #0046DB;
  font-weight: 500;
}

.data-aggregation-node li > a::before {
  content: '';
  display: inline-block;
  width: 6px;
  height: 6px;
  margin-right: 12px;
  background: #0046DB;
  border-radius: 50%;
  opacity: 0;
  transition: opacity 0.3s;
}

.data-aggregation-node li.active > a::before,
.data-aggregation-node li:hover > a::before {
  opacity: 1;
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

/* 模块内容容器 - 与左侧保持一致的视觉效果 */
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

/* 模块标题 */
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
  margin-bottom: 0;
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
}

.card-icon i {
  color: #0046DB;
  opacity: 0.8;
  transition: opacity 0.3s;
}

.data-item:hover .card-icon i {
  opacity: 1;
}

/* 面包屑导航 */
.mb-nav {
  background: #fff;
  padding: 15px 0;
  border-bottom: 1px solid #e8e8e8;
  margin-bottom: 20px;
}

.mb-nav p {
  margin: 0;
  color: #666;
  font-size: 14px;
}

.mb-nav a {
  color: #0046DB;
  text-decoration: none;
}

.mb-nav a:hover {
  text-decoration: underline;
}

.mb-nav span {
  color: #333;
}

/* 行业分布 */
.industry-distribution {
  margin-top: 30px;
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

.distribution-chart {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.distribution-bars {
  display: flex;
  height: 40px;
  border-radius: 20px;
  overflow: hidden;
  background: #f8f9fa;
}

.distribution-bar {
  height: 100%;
  background: #0046DB;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 15px;
  color: #fff;
  font-size: 12px;
  font-weight: 500;
  transition: width 0.3s;
}

.distribution-bar:hover {
  opacity: 0.9;
}

.bar-label {
  flex: 1;
}

.bar-value {
  font-weight: 700;
}

.distribution-legend {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 10px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.legend-text {
  font-size: 12px;
  color: #666;
}

/* ==================== 工艺统计 ==================== */
.process-stats {
  margin-bottom: 25px;
}

.stat-row {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.stat-box {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  text-align: center;
  border: 1px solid #f0f0f0;
  transition: all 0.3s;
}

.stat-box:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #0046DB;
}

.stat-icon {
  font-size: 28px;
  color: #0046DB;
  margin-bottom: 12px;
}

.stat-content {
  flex: 1;
}

.stat-title {
  font-size: 13px;
  color: #666;
  margin-bottom: 8px;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #0046DB;
  margin-bottom: 6px;
}

.stat-change {
  font-size: 12px;
  color: #999;
}

.stat-change.up {
  color: #f56c6c;
}

.stat-change.down {
  color: #67c23a;
}

/* 工艺流程图 */
.process-flow {
  margin-bottom: 25px;
}

.flow-diagram {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
}

.flow-steps {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.flow-step {
  display: flex;
  align-items: flex-start;
  padding: 15px;
  background: #f8f9fa;
  border-radius: 8px;
  border-left: 4px solid #0046DB;
}

.step-number {
  width: 32px;
  height: 32px;
  background: #0046DB;
  color: #fff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 15px;
  font-weight: 600;
}

.step-content h4 {
  font-size: 15px;
  color: #333;
  margin: 0 0 8px 0;
}

.step-content p {
  font-size: 13px;
  color: #666;
  margin: 0 0 10px 0;
  line-height: 1.4;
}

.step-meta {
  display: flex;
  gap: 15px;
}

.step-meta span {
  font-size: 12px;
  color: #888;
  display: flex;
  align-items: center;
  gap: 4px;
}

.step-meta i {
  color: #0046DB;
}

/* 工艺参数表格 */
.process-parameters {
  margin-bottom: 25px;
}

.parameters-table {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
  overflow-x: auto;
}

.parameters-table table {
  width: 100%;
  border-collapse: collapse;
  min-width: 800px;
}

.parameters-table th {
  padding: 14px;
  text-align: left;
  background: #fafafa;
  color: #666;
  font-weight: 500;
  font-size: 13px;
  border-bottom: 1px solid #e8e8e8;
}

.parameters-table td {
  padding: 12px;
  color: #333;
  font-size: 13px;
  border-bottom: 1px solid #e8e8e8;
}

.optimal-value {
  color: #0046DB;
  font-weight: 500;
}

/* 节能措施 */
.energy-saving {
  margin-bottom: 0;
}

.saving-measures {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.measure-card {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
  transition: all 0.3s;
  display: flex;
  flex-direction: column;
}

.measure-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #0046DB;
}

.measure-icon {
  font-size: 32px;
  color: #0046DB;
  margin-bottom: 12px;
}

.measure-content h4 {
  font-size: 16px;
  color: #333;
  margin: 0 0 8px 0;
}

.measure-content p {
  font-size: 13px;
  color: #666;
  line-height: 1.5;
  margin: 0 0 12px 0;
}

.measure-effect {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

.saving-potential,
.investment-cost {
  font-size: 12px;
  color: #666;
  display: flex;
  align-items: center;
  gap: 4px;
}

.saving-potential i,
.investment-cost i {
  color: #0046DB;
}

/* 有色金属工艺分类 */
.process-categories {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  margin-bottom: 12px;
  border: 1px solid #f0f0f0;
}

.categories-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 12px;
}

.category-card {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 15px;
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.category-card:hover,
.category-card.active {
  background: #e6f7ff;
  border-color: #0046DB;
  transform: translateY(-2px);
}

.category-icon {
  font-size: 28px;
  color: #0046DB;
  margin-bottom: 10px;
}

.category-content h4 {
  font-size: 15px;
  color: #333;
  margin: 0 0 6px 0;
}

.category-content p {
  font-size: 12px;
  color: #666;
  margin: 0 0 8px 0;
  line-height: 1.4;
}

.process-count {
  font-size: 11px;
  color: #0046DB;
  font-weight: 600;
}

/* 工艺对比表格 */
.process-comparison {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
}

.comparison-table {
  overflow-x: auto;
}

.comparison-table table {
  width: 100%;
  border-collapse: collapse;
  min-width: 800px;
}

.comparison-table th {
  padding: 14px;
  text-align: left;
  background: #fafafa;
  color: #666;
  font-weight: 500;
  font-size: 13px;
  border-bottom: 1px solid #e8e8e8;
}

.comparison-table td {
  padding: 12px;
  color: #333;
  font-size: 13px;
  border-bottom: 1px solid #e8e8e8;
}

.rating {
  color: #ffc107;
}

/* ==================== 数据库统计新增样式 ==================== */
/* 统计概览 */
.stats-overview {
  margin-bottom: 25px;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
}

.stat-card {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
  transition: all 0.3s;
  position: relative;
  overflow: hidden;
}

.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #0046DB;
}

.stat-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 4px;
  height: 100%;
  background: #0046DB;
  opacity: 0;
  transition: opacity 0.3s;
}

.stat-card:hover::before {
  opacity: 1;
}

.stat-icon {
  width: 50px;
  height: 50px;
  background: rgba(0, 70, 219, 0.1);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 15px;
}

.stat-icon i {
  font-size: 24px;
  color: #0046DB;
}

.stat-content h4 {
  font-size: 14px;
  color: #666;
  margin: 0 0 8px 0;
  font-weight: 500;
}

.stat-number {
  font-size: 26px;
  font-weight: 700;
  color: #0046DB;
  margin: 0 0 5px 0;
  line-height: 1.2;
}

.stat-content p {
  font-size: 12px;
  color: #999;
  margin: 0 0 8px 0;
}

.stat-change {
  font-size: 11px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.stat-change.up {
  color: #67c23a;
}

.stat-change.down {
  color: #f56c6c;
}

/* 数据增长趋势 */
.growth-trend {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
  margin-bottom: 25px;
}

.trend-chart-container {
  margin-top: 20px;
}

.trend-legend {
  display: flex;
  gap: 20px;
  margin-bottom: 15px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.legend-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
}

.legend-text {
  font-size: 13px;
  color: #666;
}

.trend-bars {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  height: 200px;
  padding: 20px 0;
  border-bottom: 1px solid #e8e8e8;
  position: relative;
}

.trend-month {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  height: 100%;
  position: relative;
}

.month-label {
  font-size: 12px;
  color: #666;
  position: absolute;
  bottom: -25px;
}

.bar-container {
  display: flex;
  justify-content: center;
  align-items: flex-end;
  gap: 4px;
  height: calc(100% - 25px);
  width: 30px;
  position: relative;
}

.bar-data {
  width: 12px;
  background: #0046DB;
  border-radius: 3px 3px 0 0;
  position: relative;
  transition: height 0.3s;
}

.bar-process {
  width: 12px;
  background: #00B4FF;
  border-radius: 3px 3px 0 0;
  position: relative;
  transition: height 0.3s;
}

.bar-value {
  position: absolute;
  top: -20px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 10px;
  color: #666;
  white-space: nowrap;
}

/* 数据质量分析 */
.data-quality {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
  margin-bottom: 25px;
}

.quality-metrics {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.quality-metric {
  background: #f8f9fa;
  border-radius: 8px;
  padding: 15px;
}

.metric-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.metric-title {
  font-size: 14px;
  color: #666;
  font-weight: 500;
}

.metric-value {
  font-size: 18px;
  font-weight: 700;
  color: #0046DB;
}

.metric-bar {
  height: 8px;
  background: #e8e8e8;
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: 8px;
}

.bar-fill {
  height: 100%;
  background: #0046DB;
  border-radius: 4px;
  transition: width 0.3s;
}

.metric-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
}

.metric-change {
  display: flex;
  align-items: center;
  gap: 3px;
}

.metric-change.up {
  color: #67c23a;
}

.metric-change.down {
  color: #f56c6c;
}

.metric-desc {
  color: #999;
}

/* 热门工艺访问 */
.popular-processes {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
  margin-bottom: 25px;
}

.process-ranking {
  margin-top: 15px;
}

.rank-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.rank-item {
  display: flex;
  align-items: center;
  padding: 12px 15px;
  background: #f8f9fa;
  border-radius: 6px;
  transition: all 0.3s;
}

.rank-item:hover {
  background: #e6f7ff;
  transform: translateX(5px);
}

.rank-index {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 14px;
  margin-right: 15px;
  background: #e8e8e8;
  color: #666;
}

.rank-index.rank-gold {
  background: linear-gradient(135deg, #FFD700, #FFA500);
  color: #fff;
}

.rank-index.rank-silver {
  background: linear-gradient(135deg, #C0C0C0, #A9A9A9);
  color: #fff;
}

.rank-index.rank-bronze {
  background: linear-gradient(135deg, #CD7F32, #A0522D);
  color: #fff;
}

.rank-content {
  flex: 1;
}

.rank-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.rank-industry {
  font-size: 11px;
  color: #666;
  background: rgba(0, 70, 219, 0.1);
  padding: 2px 6px;
  border-radius: 4px;
  display: inline-block;
}

.rank-stats {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 4px;
}

.rank-views {
  font-size: 13px;
  color: #666;
  display: flex;
  align-items: center;
  gap: 5px;
}

.rank-views i {
  color: #0046DB;
}

.rank-change {
  font-size: 11px;
  display: flex;
  align-items: center;
  gap: 3px;
}

.rank-change.up {
  color: #67c23a;
}

.rank-change.down {
  color: #f56c6c;
}

/* 数据来源分布 */
.data-sources {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
}

.sources-chart {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
  align-items: center;
  margin-top: 15px;
}

.sources-visual {
  display: flex;
  justify-content: center;
  align-items: center;
}

.donut-chart {
  width: 200px;
  height: 200px;
  position: relative;
  border-radius: 50%;
  background: conic-gradient(
      var(--color, #0046DB) calc(var(--percentage, 0) * 3.6deg),
      transparent 0 360deg
  );
  display: flex;
  align-items: center;
  justify-content: center;
}

.donut-segment:nth-child(1) {
  --percentage: 38;
  --color: #0046DB;
}

.donut-segment:nth-child(2) {
  --percentage: 25;
  --color: #00B4FF;
}

.donut-segment:nth-child(3) {
  --percentage: 22;
  --color: #4ECDC4;
}

.donut-segment:nth-child(4) {
  --percentage: 15;
  --color: #96CEB4;
}

.donut-center {
  width: 120px;
  height: 120px;
  background: #fff;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.center-value {
  font-size: 24px;
  font-weight: 700;
  color: #0046DB;
}

.center-label {
  font-size: 12px;
  color: #666;
}

.sources-legend {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.legend-item {
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
  border-left: 4px solid transparent;
  transition: all 0.3s;
}

.legend-item:hover {
  background: #e6f7ff;
  transform: translateX(5px);
}

.legend-item:nth-child(1) {
  border-left-color: #0046DB;
}

.legend-item:nth-child(2) {
  border-left-color: #00B4FF;
}

.legend-item:nth-child(3) {
  border-left-color: #4ECDC4;
}

.legend-item:nth-child(4) {
  border-left-color: #96CEB4;
}

.legend-header {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  margin-right: 8px;
}

.legend-text {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  flex: 1;
}

.legend-percentage {
  font-size: 16px;
  font-weight: 700;
  color: #0046DB;
}

.legend-desc {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.legend-count {
  font-size: 11px;
  color: #999;
}

/* 表单样式 */
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

.form-group select option {
  background: #fff;
  color: #333;
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
  justify-content: center;
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

/* 化工工艺搜索结果 */
.chemical-results {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chemical-card {
  background: #fff;
  border-radius: 6px;
  padding: 15px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
  transition: all 0.3s;
}

.chemical-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #0046DB;
}

.chemical-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.chemical-header h4 {
  font-size: 15px;
  color: #333;
  margin: 0;
  flex: 1;
}

.chemical-tag {
  font-size: 10px;
  color: #0046DB;
  background: rgba(0, 70, 219, 0.1);
  padding: 2px 6px;
  border-radius: 8px;
  font-weight: 500;
}

.chemical-info {
  display: flex;
  gap: 15px;
  margin-bottom: 8px;
  font-size: 12px;
  color: #666;
}

.chemical-info span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.chemical-info i {
  color: #0046DB;
}

.chemical-desc {
  font-size: 13px;
  color: #666;
  line-height: 1.5;
  margin: 0 0 10px 0;
}

.chemical-metrics {
  display: flex;
  gap: 12px;
  margin-bottom: 10px;
}

.metric {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #666;
}

.metric i {
  color: #0046DB;
}

/* 优化案例 */
.case-categories {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  margin-bottom: 12px;
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

.case-list {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
}

.list-controls {
  display: flex;
  gap: 8px;
  align-items: center;
}

.list-controls input {
  padding: 7px 10px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 13px;
  flex: 1;
  max-width: 300px;
}

.list-controls select {
  padding: 7px 10px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 13px;
  background: #fff;
  cursor: pointer;
}

.case-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 15px;
}

.case-card {
  background: #fff;
  border-radius: 6px;
  padding: 15px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
  transition: all 0.3s;
}

.case-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #0046DB;
}

.case-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.case-header h4 {
  font-size: 15px;
  color: #333;
  margin: 0;
  flex: 1;
}

.case-industry {
  font-size: 10px;
  color: #fff;
  background: #0046DB;
  padding: 2px 6px;
  border-radius: 8px;
  font-weight: 500;
}

.case-meta {
  display: flex;
  gap: 15px;
  font-size: 11px;
  color: #999;
  margin-bottom: 8px;
}

.case-meta span {
  display: flex;
  align-items: center;
  gap: 3px;
}

.case-content p {
  font-size: 13px;
  color: #666;
  line-height: 1.5;
  margin: 0 0 12px 0;
}

.case-effects {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 10px;
  margin-bottom: 10px;
}

.effect-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.effect-item i {
  font-size: 18px;
  color: #0046DB;
}

.effect-title {
  font-size: 11px;
  color: #999;
}

.effect-value {
  font-size: 13px;
  color: #333;
  font-weight: 500;
}

/* 按钮样式 */
.btn-search, .btn-reset, .btn-export, .btn-detail, .btn-download {
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
  display: flex;
  align-items: center;
  gap: 6px;
}

.btn-search {
  background: #0046DB;
  color: #fff;
  border: 1px solid #0046DB;
}

.btn-search:hover {
  background: #003db9;
}

.btn-reset {
  background: transparent;
  color: #666;
  border: 1px solid #dcdfe6;
}

.btn-reset:hover {
  background: #f8f9fa;
}

.btn-export {
  background: rgba(0, 70, 219, 0.1);
  color: #0046DB;
  border: 1px solid rgba(0, 70, 219, 0.3);
}

.btn-export:hover {
  background: rgba(0, 70, 219, 0.2);
}

.btn-detail {
  background: transparent;
  color: #666;
  border: 1px solid #dcdfe6;
}

.btn-detail:hover {
  background: rgba(0, 70, 219, 0.1);
  color: #0046DB;
  border-color: rgba(0, 70, 219, 0.3);
}

.btn-download {
  background: transparent;
  color: #666;
  border: 1px solid #dcdfe6;
}

.btn-download:hover {
  color: #4CAF50;
  border-color: #4CAF50;
  background: rgba(76, 175, 80, 0.05);
}

/* 工具类 */
.mt30 { margin-top: 30px; }

/* 响应式设计 */
@media (max-width: 1200px) {
  .container {
    max-width: 960px;
  }

  .echarts-data-num {
    grid-template-columns: repeat(2, 1fr);
  }

  .stat-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .saving-measures {
    grid-template-columns: 1fr;
  }

  .categories-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .quality-metrics {
    grid-template-columns: 1fr;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .sources-chart {
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

  .process-data {
    padding-top: 80px;
  }
}

@media (max-width: 768px) {
  .main-content {
    padding: 15px 0 25px;
  }

  .module-content {
    padding: 15px;
    min-height: auto;
  }

  .echarts-data-num {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .stat-row {
    grid-template-columns: 1fr;
    gap: 10px;
  }

  .categories-grid {
    grid-template-columns: 1fr;
  }

  .saving-measures {
    grid-template-columns: 1fr;
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

  .stat-value {
    font-size: 20px;
  }

  .form-row {
    grid-template-columns: 1fr;
  }

  .case-effects {
    grid-template-columns: 1fr;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .quality-metrics {
    grid-template-columns: 1fr;
  }

  .donut-chart {
    width: 150px;
    height: 150px;
  }

  .donut-center {
    width: 90px;
    height: 90px;
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

  .chemical-info {
    flex-direction: column;
    gap: 5px;
  }

  .case-meta {
    flex-direction: column;
    gap: 5px;
  }

  .form-actions {
    flex-wrap: wrap;
  }

  .btn-search,
  .btn-reset {
    flex: 1;
    min-width: 120px;
  }

  .sources-chart {
    gap: 15px;
  }

  .donut-chart {
    width: 120px;
    height: 120px;
  }

  .donut-center {
    width: 70px;
    height: 70px;
  }

  .center-value {
    font-size: 18px;
  }

  .center-label {
    font-size: 10px;
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
.stat-box,
.measure-card,
.category-card,
.chemical-card,
.case-card,
.stat-card,
.quality-metric,
.rank-item,
.legend-item {
  animation: fadeIn 0.3s ease-out;
}
</style>