<template>
  <Header></Header>
  <div class="thermodynamics">
    <!-- 面包屑导航 -->
    <div class="mb-nav">
      <div class="container">
        <p>
          当前位置： <router-link to="/">首页</router-link> >
          <span>冶金热/动力学</span>
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
                :class="{active: activeCategory === 'thermo'}"
                @click="switchCategory('thermo')">
              <dt class="index1">
                <a href="javascript:void(0)">热力学数据库</a>
              </dt>
            </dl>

            <dl class="data-aggregation-nav"
                :class="{active: activeCategory === 'kinetics'}"
                @click="switchCategory('kinetics')">
              <dt class="index2">
                <a href="javascript:void(0)">动力学数据库</a>
              </dt>
            </dl>

            <dl class="data-aggregation-nav"
                :class="{active: activeCategory === 'phase'}"
                @click="switchCategory('phase')">
              <dt class="index3">
                <a href="javascript:void(0)">相图数据库</a>
              </dt>
            </dl>

            <dl class="data-aggregation-nav"
                :class="{active: activeCategory === 'reaction'}"
                @click="switchCategory('reaction')">
              <dt class="index4">
                <a href="javascript:void(0)">反应数据库</a>
              </dt>
            </dl>

            <!-- 功能模块 -->
            <dl class="data-aggregation-nav"
                :class="{active: activeCategory === 'features'}"
                @click="switchCategory('features')">
              <dt class="index5">
                <a href="javascript:void(0)">功能模块</a>
              </dt>
            </dl>

            <!-- 数据库统计 -->
            <dl class="data-aggregation-nav"
                :class="{active: activeCategory === 'stats'}"
                @click="switchCategory('stats')">
              <dt class="index6">
                <a href="javascript:void(0)">数据库统计</a>
              </dt>
            </dl>
          </div>
          <div class="m-nav-but">点击展开菜单</div>
        </div>

        <!-- 右侧内容展示区 -->
        <div class="data-aggregation-right">
          <!-- ==================== 数据库概览 ==================== -->
          <div class="module-content" v-if="activeCategory === 'thermo'">
            <div class="module-header">
              <h2><i class="fas fa-temperature-high"></i> 热力学数据库</h2>
              <p class="module-desc">相图、热容、焓、熵等热力学性质数据，支持冶金过程模拟与优化</p>
            </div>

            <!-- 关键指标 -->
            <div class="echarts-data-num">
              <div class="data-item">
                <dl>
                  <dt>数据记录数</dt>
                  <dd>12,500+</dd>
                  <dd class="trend up">持续更新</dd>
                </dl>
                <div class="card-icon">
                  <i class="fas fa-database fa-2x"></i>
                </div>
              </div>

              <div class="data-item">
                <dl>
                  <dt>合金体系</dt>
                  <dd>50+</dd>
                  <dd class="trend up">持续增加</dd>
                </dl>
                <div class="card-icon">
                  <i class="fas fa-industry fa-2x"></i>
                </div>
              </div>

              <div class="data-item">
                <dl>
                  <dt>数据准确度</dt>
                  <dd>99.5%</dd>
                  <dd class="trend down">误差 ±0.1%</dd>
                </dl>
                <div class="card-icon">
                  <i class="fas fa-check-circle fa-2x"></i>
                </div>
              </div>
            </div>

            <!-- 数据查询 -->
            <div class="search-section mt30">
              <div class="section-header">
                <h3><i class="fas fa-search"></i> 数据查询</h3>
                <p>选择查询条件，检索冶金热力学数据</p>
              </div>

              <div class="search-form">
                <div class="form-row">
                  <div class="form-group">
                    <label for="system"><i class="fas fa-cogs"></i> 合金体系</label>
                    <select id="system" v-model="searchParams.system">
                      <option value="">选择合金体系</option>
                      <option value="fe-c">Fe-C 体系</option>
                      <option value="fe-cr">Fe-Cr 体系</option>
                      <option value="al-cu">Al-Cu 体系</option>
                      <option value="ni-cr">Ni-Cr 体系</option>
                      <option value="ti-al">Ti-Al 体系</option>
                      <option value="cu-zn">Cu-Zn 体系</option>
                    </select>
                  </div>

                  <div class="form-group">
                    <label for="property"><i class="fas fa-chart-line"></i> 物性类型</label>
                    <select id="property" v-model="searchParams.property">
                      <option value="">选择物性类型</option>
                      <option value="enthalpy">生成焓</option>
                      <option value="entropy">熵</option>
                      <option value="heat_capacity">热容</option>
                      <option value="phase_diagram">相图数据</option>
                    </select>
                  </div>

                  <div class="form-group">
                    <label for="temperature"><i class="fas fa-thermometer-half"></i> 温度范围 (K)</label>
                    <div class="range-input">
                      <input type="number" v-model="searchParams.tempMin" placeholder="最小值">
                      <span>至</span>
                      <input type="number" v-model="searchParams.tempMax" placeholder="最大值">
                    </div>
                  </div>
                </div>

                <div class="form-actions">
                  <button class="btn-search" @click="searchData">
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
                <h3><i class="fas fa-table"></i> 查询结果</h3>
                <div class="results-info">
                  <span>共找到 {{ results.length }} 条记录</span>
                  <button class="btn-export" @click="exportData">
                    <i class="fas fa-download"></i> 导出数据
                  </button>
                </div>
              </div>

              <div class="results-table">
                <table>
                  <thead>
                  <tr>
                    <th>合金体系</th>
                    <th>物性类型</th>
                    <th>温度 (K)</th>
                    <th>数值</th>
                    <th>单位</th>
                    <th>数据来源</th>
                    <th>操作</th>
                  </tr>
                  </thead>
                  <tbody>
                  <tr v-for="(item, index) in paginatedResults" :key="index">
                    <td>{{ item.system }}</td>
                    <td>{{ item.property }}</td>
                    <td>{{ item.temperature }}</td>
                    <td class="value-cell">{{ item.value }}</td>
                    <td>{{ item.unit }}</td>
                    <td>{{ item.source }}</td>
                    <td>
                      <button class="btn-detail" @click="viewDetail(item)">
                        <i class="fas fa-info-circle"></i> 详情
                      </button>
                    </td>
                  </tr>
                  </tbody>
                </table>

                <!-- 分页 -->
                <div class="pagination" v-if="results.length > pageSize">
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
          </div>

          <!-- ==================== 动力学数据库 ==================== -->
          <div class="module-content" v-if="activeCategory === 'kinetics'">
            <div class="module-header">
              <h2><i class="fas fa-tachometer-alt"></i> 动力学数据库</h2>
              <p class="module-desc">扩散系数、反应速率、转变动力学数据，支持冶金过程模拟</p>
            </div>

            <!-- 关键指标 -->
            <div class="echarts-data-num">
              <div class="data-item">
                <dl>
                  <dt>数据记录数</dt>
                  <dd>8,300+</dd>
                  <dd class="trend up">持续更新</dd>
                </dl>
                <div class="card-icon">
                  <i class="fas fa-database fa-2x"></i>
                </div>
              </div>

              <div class="data-item">
                <dl>
                  <dt>反应体系</dt>
                  <dd>120+</dd>
                  <dd class="trend up">持续增加</dd>
                </dl>
                <div class="card-icon">
                  <i class="fas fa-flask fa-2x"></i>
                </div>
              </div>

              <div class="data-item">
                <dl>
                  <dt>温度范围</dt>
                  <dd>298-2000K</dd>
                  <dd class="trend down">覆盖全面</dd>
                </dl>
                <div class="card-icon">
                  <i class="fas fa-thermometer-three-quarters fa-2x"></i>
                </div>
              </div>
            </div>

            <!-- 动力学模拟功能 -->
            <div class="features-section mt30">
              <div class="section-header">
                <h3><i class="fas fa-chart-area"></i> 动力学模拟功能</h3>
                <p>基于动力学参数的冶金过程模拟，预测微观组织演变</p>
              </div>

              <div class="features-grid">
                <div class="feature-card">
                  <div class="feature-icon">
                    <i class="fas fa-wave-square"></i>
                  </div>
                  <h4>扩散过程模拟</h4>
                  <p>模拟原子扩散过程，预测浓度分布</p>
                </div>

                <div class="feature-card">
                  <div class="feature-icon">
                    <i class="fas fa-exchange-alt"></i>
                  </div>
                  <h4>相变动力学预测</h4>
                  <p>预测相变过程，计算转变速率</p>
                </div>

                <div class="feature-card">
                  <div class="feature-icon">
                    <i class="fas fa-expand-alt"></i>
                  </div>
                  <h4>晶粒长大模拟</h4>
                  <p>模拟晶粒生长过程，预测组织演变</p>
                </div>

                <div class="feature-card">
                  <div class="feature-icon">
                    <i class="fas fa-bolt"></i>
                  </div>
                  <h4>反应速率计算</h4>
                  <p>计算化学反应速率，优化工艺参数</p>
                </div>
              </div>
            </div>
          </div>

          <!-- ==================== 相图数据库 ==================== -->
          <div class="module-content" v-if="activeCategory === 'phase'">
            <div class="module-header">
              <h2><i class="fas fa-chart-pie"></i> 相图数据库</h2>
              <p class="module-desc">二元、三元及多元合金相图数据，支持相图计算与可视化</p>
            </div>

            <!-- 关键指标 -->
            <div class="echarts-data-num">
              <div class="data-item">
                <dl>
                  <dt>相图数量</dt>
                  <dd>5,200+</dd>
                  <dd class="trend up">持续更新</dd>
                </dl>
                <div class="card-icon">
                  <i class="fas fa-chart-pie fa-2x"></i>
                </div>
              </div>

              <div class="data-item">
                <dl>
                  <dt>元素体系</dt>
                  <dd>30+</dd>
                  <dd class="trend up">持续增加</dd>
                </dl>
                <div class="card-icon">
                  <i class="fas fa-atom fa-2x"></i>
                </div>
              </div>

              <div class="data-item">
                <dl>
                  <dt>相图类型</dt>
                  <dd>二元/三元/多元</dd>
                  <dd class="trend down">覆盖全面</dd>
                </dl>
                <div class="card-icon">
                  <i class="fas fa-layer-group fa-2x"></i>
                </div>
              </div>
            </div>

            <!-- 相图可视化 -->
            <div class="phase-visualization mt30">
              <div class="section-header">
                <h3><i class="fas fa-eye"></i> 相图可视化</h3>
                <p>交互式相图展示与分析工具</p>
              </div>

              <div class="visualization-container">
                <div class="mock-phase-diagram">
                  <div class="phase-diagram">
                    <!-- 模拟相图 -->
                    <div class="phase-region liquid" style="top: 10%; left: 20%; width: 60%; height: 40%">
                      <span class="region-label">液相区</span>
                    </div>
                    <div class="phase-region solid" style="top: 50%; left: 20%; width: 60%; height: 40%">
                      <span class="region-label">固相区</span>
                    </div>
                    <div class="phase-line" style="top: 50%; left: 20%; width: 60%"></div>
                  </div>
                  <div class="phase-legend">
                    <div class="legend-item">
                      <span class="legend-color" style="background-color: #0046DB"></span>
                      <span class="legend-text">液相区</span>
                    </div>
                    <div class="legend-item">
                      <span class="legend-color" style="background-color: #00B4FF"></span>
                      <span class="legend-text">固相区</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- ==================== 反应数据库 ==================== -->
          <div class="module-content" v-if="activeCategory === 'reaction'">
            <div class="module-header">
              <h2><i class="fas fa-atom"></i> 反应数据库</h2>
              <p class="module-desc">冶金反应热力学与动力学参数，支持反应过程优化</p>
            </div>

            <!-- 关键指标 -->
            <div class="echarts-data-num">
              <div class="data-item">
                <dl>
                  <dt>数据记录数</dt>
                  <dd>3,800+</dd>
                  <dd class="trend up">持续更新</dd>
                </dl>
                <div class="card-icon">
                  <i class="fas fa-database fa-2x"></i>
                </div>
              </div>

              <div class="data-item">
                <dl>
                  <dt>反应类型</dt>
                  <dd>200+</dd>
                  <dd class="trend up">持续增加</dd>
                </dl>
                <div class="card-icon">
                  <i class="fas fa-bolt fa-2x"></i>
                </div>
              </div>

              <div class="data-item">
                <dl>
                  <dt>反应体系</dt>
                  <dd>50+</dd>
                  <dd class="trend down">覆盖全面</dd>
                </dl>
                <div class="card-icon">
                  <i class="fas fa-industry fa-2x"></i>
                </div>
              </div>
            </div>

            <!-- 反应热力学计算 -->
            <div class="reaction-calculations mt30">
              <div class="section-header">
                <h3><i class="fas fa-calculator"></i> 反应热力学计算</h3>
                <p>基于数据库的热力学参数计算，支持反应过程优化</p>
              </div>

              <div class="calculations-grid">
                <div class="calculation-card">
                  <div class="calc-icon">
                    <i class="fas fa-balance-scale"></i>
                  </div>
                  <div class="calc-content">
                    <h4>Gibbs自由能计算</h4>
                    <p>计算反应的Gibbs自由能变化</p>
                    <button class="btn-detail" @click="openCalculator('gibbs')">开始计算</button>
                  </div>
                </div>

                <div class="calculation-card">
                  <div class="calc-icon">
                    <i class="fas fa-fire"></i>
                  </div>
                  <div class="calc-content">
                    <h4>反应焓变计算</h4>
                    <p>计算反应的热效应</p>
                    <button class="btn-detail" @click="openCalculator('enthalpy')">开始计算</button>
                  </div>
                </div>

                <div class="calculation-card">
                  <div class="calc-icon">
                    <i class="fas fa-chart-line"></i>
                  </div>
                  <div class="calc-content">
                    <h4>平衡常数计算</h4>
                    <p>计算反应平衡常数</p>
                    <button class="btn-detail" @click="openCalculator('equilibrium')">开始计算</button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- ==================== 功能模块 ==================== -->
          <div class="module-content" v-if="activeCategory === 'features'">
            <div class="module-header">
              <h2><i class="fas fa-cogs"></i> 数据库功能模块</h2>
              <p class="module-desc">全面的冶金热/动力学计算与模拟功能</p>
            </div>

            <div class="features-grid">
              <div class="feature-card">
                <div class="feature-icon">
                  <i class="fas fa-calculator"></i>
                </div>
                <h4>热力学计算</h4>
                <p>基于数据库的热力学参数计算，支持相图预测、反应焓变计算等</p>
                <ul class="feature-list">
                  <li>Gibbs自由能计算</li>
                  <li>活度系数预测</li>
                  <li>相平衡计算</li>
                </ul>
              </div>

              <div class="feature-card">
                <div class="feature-icon">
                  <i class="fas fa-chart-area"></i>
                </div>
                <h4>动力学模拟</h4>
                <p>基于动力学参数的冶金过程模拟，预测微观组织演变</p>
                <ul class="feature-list">
                  <li>扩散过程模拟</li>
                  <li>相变动力学预测</li>
                  <li>晶粒长大模拟</li>
                </ul>
              </div>

              <div class="feature-card">
                <div class="feature-icon">
                  <i class="fas fa-project-diagram"></i>
                </div>
                <h4>可视化分析</h4>
                <p>数据可视化与交互分析，生成专业图表与报告</p>
                <ul class="feature-list">
                  <li>相图可视化</li>
                  <li>趋势分析图表</li>
                  <li>自定义数据对比</li>
                </ul>
              </div>

              <div class="feature-card">
                <div class="feature-icon">
                  <i class="fas fa-robot"></i>
                </div>
                <h4>AI预测</h4>
                <p>基于机器学习的物性预测与优化推荐</p>
                <ul class="feature-list">
                  <li>物性参数预测</li>
                  <li>合金设计优化</li>
                  <li>工艺参数推荐</li>
                </ul>
              </div>
            </div>
          </div>

          <!-- ==================== 数据库统计 ==================== -->
          <div class="module-content" v-if="activeCategory === 'stats'">
            <div class="module-header">
              <h2><i class="fas fa-chart-bar"></i> 数据库统计信息</h2>
              <p class="module-desc">全面的冶金热/动力学数据库统计概览</p>
            </div>

            <div class="stats-grid">
              <div class="stat-card">
                <div class="stat-icon">
                  <i class="fas fa-database"></i>
                </div>
                <div class="stat-content">
                  <h4>数据总量</h4>
                  <div class="stat-number">29,800+</div>
                  <p>条热/动力学数据记录</p>
                </div>
              </div>

              <div class="stat-card">
                <div class="stat-icon">
                  <i class="fas fa-atom"></i>
                </div>
                <div class="stat-content">
                  <h4>合金体系</h4>
                  <div class="stat-number">80+</div>
                  <p>个二元及多元合金体系</p>
                </div>
              </div>

              <div class="stat-card">
                <div class="stat-icon">
                  <i class="fas fa-thermometer-three-quarters"></i>
                </div>
                <div class="stat-content">
                  <h4>温度范围</h4>
                  <div class="stat-number">298-2000K</div>
                  <p>覆盖常温至高温范围</p>
                </div>
              </div>

              <div class="stat-card">
                <div class="stat-icon">
                  <i class="fas fa-industry"></i>
                </div>
                <div class="stat-content">
                  <h4>应用案例</h4>
                  <div class="stat-number">150+</div>
                  <p>个实际冶金工艺优化案例</p>
                </div>
              </div>
            </div>

            <!-- 数据分布 -->
            <div class="data-distribution mt30">
              <div class="section-header">
                <h3><i class="fas fa-chart-pie"></i> 数据分布情况</h3>
                <p>各类型数据占比与分布情况</p>
              </div>

              <div class="distribution-chart">
                <div class="distribution-bars">
                  <div class="distribution-bar" style="width: 42%" title="热力学数据: 42%">
                    <span class="bar-label">热力学数据</span>
                    <span class="bar-value">42%</span>
                  </div>
                  <div class="distribution-bar" style="width: 28%; background-color: #00B4FF" title="动力学数据: 28%">
                    <span class="bar-label">动力学数据</span>
                    <span class="bar-value">28%</span>
                  </div>
                  <div class="distribution-bar" style="width: 18%; background-color: #4ECDC4" title="相图数据: 18%">
                    <span class="bar-label">相图数据</span>
                    <span class="bar-value">18%</span>
                  </div>
                  <div class="distribution-bar" style="width: 12%; background-color: #96CEB4" title="反应数据: 12%">
                    <span class="bar-label">反应数据</span>
                    <span class="bar-value">12%</span>
                  </div>
                </div>
                <div class="distribution-legend">
                  <div class="legend-item">
                    <span class="legend-color" style="background-color: #0046DB"></span>
                    <span class="legend-text">热力学数据 (42%)</span>
                  </div>
                  <div class="legend-item">
                    <span class="legend-color" style="background-color: #00B4FF"></span>
                    <span class="legend-text">动力学数据 (28%)</span>
                  </div>
                  <div class="legend-item">
                    <span class="legend-color" style="background-color: #4ECDC4"></span>
                    <span class="legend-text">相图数据 (18%)</span>
                  </div>
                  <div class="legend-item">
                    <span class="legend-color" style="background-color: #96CEB4"></span>
                    <span class="legend-text">反应数据 (12%)</span>
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
  name: "ThermodynamicsDatabase",
  components: {
    Header,
    Footer,
  },
  data() {
    return {
      activeCategory: 'thermo',
      searchParams: {
        system: '',
        property: '',
        tempMin: '',
        tempMax: ''
      },
      showResults: false,
      results: [],
      currentPage: 1,
      pageSize: 10
    };
  },
  computed: {
    totalPages() {
      return Math.ceil(this.results.length / this.pageSize);
    },
    paginatedResults() {
      const start = (this.currentPage - 1) * this.pageSize;
      const end = start + this.pageSize;
      return this.results.slice(start, end);
    }
  },
  methods: {
    switchCategory(category) {
      this.activeCategory = category;
    },

    searchData() {
      this.showResults = true;
      this.currentPage = 1;

      this.results = [
        { system: 'Fe-C', property: '生成焓', temperature: 298, value: -27.3, unit: 'kJ/mol', source: 'CALPHAD' },
        { system: 'Fe-C', property: '生成焓', temperature: 500, value: -25.8, unit: 'kJ/mol', source: 'CALPHAD' },
        { system: 'Fe-Cr', property: '扩散系数', temperature: 1000, value: '2.3e-11', unit: 'm²/s', source: '实验数据' },
        { system: 'Al-Cu', property: '相图数据', temperature: 823, value: 'θ-Al₂Cu', unit: '相组成', source: '实验测定' },
        { system: 'Ni-Cr', property: '热容', temperature: 300, value: 24.5, unit: 'J/(mol·K)', source: '第一性原理' },
        { system: 'Ti-Al', property: '反应速率', temperature: 1200, value: 0.045, unit: 'mol/(m²·s)', source: '动力学模拟' },
        { system: 'Cu-Zn', property: '熵', temperature: 298, value: 41.5, unit: 'J/(mol·K)', source: '热力学数据库' },
        { system: 'Fe-C', property: '扩散系数', temperature: 800, value: '5.6e-12', unit: 'm²/s', source: '实验数据' },
        { system: 'Fe-Cr', property: '生成焓', temperature: 298, value: -15.2, unit: 'kJ/mol', source: 'CALPHAD' },
        { system: 'Al-Cu', property: '扩散系数', temperature: 773, value: '3.2e-13', unit: 'm²/s', source: '实验数据' },
        { system: 'Ni-Cr', property: '相图数据', temperature: 1473, value: 'γ-Ni固溶体', unit: '相组成', source: '实验测定' },
        { system: 'Ti-Al', property: '热容', temperature: 500, value: 28.7, unit: 'J/(mol·K)', source: '第一性原理' },
      ];
    },

    resetSearch() {
      this.searchParams = {
        system: '',
        property: '',
        tempMin: '',
        tempMax: ''
      };
      this.showResults = false;
      this.results = [];
      this.currentPage = 1;
    },

    exportData() {
      alert('数据导出功能开发中...');
    },

    viewDetail(item) {
      alert(`查看详情：\n合金体系：${item.system}\n物性类型：${item.property}\n温度：${item.temperature}K\n数值：${item.value} ${item.unit}`);
    },

    openCalculator(type) {
      alert(`打开${type}计算器...`);
    }
  },
  mounted() {
    this.searchData();
  }
};
</script>

<style scoped>
/* ==================== 基础样式 ==================== */
.thermodynamics {
  background-color: #f5f7fa;
  min-height: 100vh;
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
  padding: 20px 0 30px;
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

.form-group select option {
  background: #fff;
  color: #333;
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

/* ==================== 功能模块 ==================== */
.features-section {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  margin-bottom: 20px;
  border: 1px solid #f0f0f0;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 15px;
}

.feature-card {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 15px;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.feature-card:hover {
  background: #e6f7ff;
  border-color: #0046DB;
  transform: translateY(-2px);
}

.feature-icon {
  font-size: 28px;
  color: #0046DB;
  margin-bottom: 10px;
}

.feature-card h4 {
  font-size: 15px;
  color: #333;
  margin: 0 0 6px 0;
}

.feature-card p {
  font-size: 13px;
  color: #666;
  margin: 0 0 8px 0;
  line-height: 1.4;
}

.feature-list {
  list-style: none;
  padding: 0;
  margin: 0;
}

.feature-list li {
  color: #666;
  font-size: 12px;
  padding: 4px 0;
  position: relative;
  padding-left: 20px;
}

.feature-list li:before {
  content: "•";
  color: #0046DB;
  position: absolute;
  left: 0;
}

/* ==================== 相图可视化 ==================== */
.phase-visualization {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
}

.visualization-container {
  position: relative;
  height: 300px;
  background: #fafafa;
  border-radius: 6px;
  overflow: hidden;
}

.mock-phase-diagram {
  width: 100%;
  height: 100%;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.phase-diagram {
  width: 80%;
  height: 80%;
  position: relative;
  border: 2px solid #e8e8e8;
  background: #fff;
}

.phase-region {
  position: absolute;
  border: 1px solid #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-weight: 500;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.phase-region.liquid {
  background: #0046DB;
}

.phase-region.solid {
  background: #00B4FF;
}

.phase-line {
  position: absolute;
  height: 2px;
  background: #ff6b6b;
  border: none;
}

.region-label {
  font-size: 14px;
  font-weight: 600;
}

.phase-legend {
  position: absolute;
  top: 10px;
  right: 10px;
  background: rgba(255, 255, 255, 0.9);
  padding: 10px;
  border-radius: 6px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.1);
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
  margin-bottom: 5px;
}

.legend-color {
  width: 12px;
  height: 12px;
  border-radius: 2px;
}

.legend-text {
  font-size: 12px;
  color: #333;
}

/* ==================== 反应计算 ==================== */
.reaction-calculations {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
}

.calculations-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
}

.calculation-card {
  background: #f8f9fa;
  border-radius: 6px;
  padding: 15px;
  text-align: center;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.calculation-card:hover {
  background: #e6f7ff;
  border-color: #0046DB;
  transform: translateY(-2px);
}

.calc-icon {
  font-size: 32px;
  color: #0046DB;
  margin-bottom: 10px;
}

.calc-content h4 {
  font-size: 15px;
  color: #333;
  margin: 0 0 6px 0;
}

.calc-content p {
  font-size: 13px;
  color: #666;
  margin: 0 0 10px 0;
  line-height: 1.4;
}

/* ==================== 数据库统计 ==================== */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 15px;
  margin-bottom: 20px;
}

.stat-card {
  background: #fff;
  border-radius: 10px;
  padding: 15px;
  text-align: center;
  transition: all 0.3s;
  border: 1px solid #f0f0f0;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #0046DB;
}

.stat-icon {
  font-size: 32px;
  color: #0046DB;
  margin-bottom: 12px;
}

.stat-content h4 {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
}

.stat-number {
  font-size: 24px;
  font-weight: 700;
  color: #0046DB;
  margin-bottom: 6px;
}

.stat-card p {
  font-size: 12px;
  color: #999;
}

/* ==================== 数据分布 ==================== */
.data-distribution {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
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

/* ==================== 响应式设计 ==================== */
@media (max-width: 1200px) {
  .container {
    max-width: 960px;
  }

  .echarts-data-num {
    grid-template-columns: repeat(2, 1fr);
  }

  .features-grid {
    grid-template-columns: 1fr;
  }

  .calculations-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
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

  .thermodynamics {
    padding-top: 80px;
  }
}

@media (max-width: 768px) {
  .form-row {
    grid-template-columns: 1fr;
  }

  .calculations-grid {
    grid-template-columns: 1fr;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .distribution-legend {
    grid-template-columns: 1fr;
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
.feature-card,
.stat-card,
.calculation-card {
  animation: fadeIn 0.3s ease-out;
}

/* 工具类 */
.mt30 { margin-top: 30px; }
</style>