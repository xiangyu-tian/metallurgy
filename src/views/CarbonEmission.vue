<template>
  <Header></Header>
  <div class="carbon-emission">
    <!-- 面包屑导航 -->
    <div class="mb-nav">
      <div class="container">
        <p>
          当前位置： <router-link to="/">首页</router-link> >
          <span>碳排放数据库</span>
        </p>
      </div>
    </div>

    <!-- 主内容区域 -->
    <div class="container main-content">
      <div class="data-aggregation">
        <!-- 左侧导航栏 -->
        <div class="data-aggregation-left">
          <div class="left-sub-nav-box">
            <!-- 数据概览模块 -->
            <dl class="data-aggregation-nav"
                :class="{active: activeModule === 'overview'}"
                @click="switchModule('overview')">
              <dt class="index1">
                <a href="javascript:void(0)">碳排放概览</a>
              </dt>
            </dl>

            <!-- 行业分析模块 -->
            <dl class="data-aggregation-nav"
                :class="{active: activeModule === 'industry'}"
                @click="switchModule('industry')">
              <dt class="index2">
                <a href="javascript:void(0)">行业碳排放分析</a>
                <p>
                  <i :style="{transform: (activeModule === 'industry' && isIndustryMenuExpanded) ? 'rotate(180deg)' : 'rotate(0deg)'}"></i>
                </p>
              </dt>              <!-- 修改这里：使用 isIndustryMenuExpanded 控制显示 -->
              <dd :style="{display: (activeModule === 'industry' && isIndustryMenuExpanded) ? 'block' : 'none'}">
                <ul class="data-aggregation-node">
                  <li v-for="item in industryList"
                      :key="item.id"
                      :class="{active: activeIndustry === item.id}"
                      @click.stop="switchIndustry(item.id)">
                    <a href="javascript:void(0)">{{ item.name }}</a>
                  </li>
                </ul>
              </dd>
            </dl>

            <!-- 区域分布模块 -->
            <dl class="data-aggregation-nav"
                :class="{active: activeModule === 'region'}"
                @click="switchModule('region')">
              <dt class="index3">
                <a href="javascript:void(0)">区域碳排放分布</a>
              </dt>
            </dl>

            <!-- 减排技术模块 -->
            <dl class="data-aggregation-nav"
                :class="{active: activeModule === 'technology'}"
                @click="switchModule('technology')">
              <dt class="index4">
                <a href="javascript:void(0)">碳减排技术库</a>
              </dt>
            </dl>

            <!-- 政策法规模块 -->
            <dl class="data-aggregation-nav"
                :class="{active: activeModule === 'policy'}"
                @click="switchModule('policy')">
              <dt class="index6">
                <a href="javascript:void(0)">政策法规库</a>
              </dt>
            </dl>
          </div>
          <div class="m-nav-but">点击展开菜单</div>
        </div>

        <!-- 右侧内容展示区 - 根据模块切换 -->
        <div class="data-aggregation-right">

          <!-- ==================== 数据概览模块 ==================== -->
          <div class="module-content" v-if="activeModule === 'overview'">
            <!-- 模块标题 -->
            <div class="module-header">
              <h2><i class="fas fa-chart-bar"></i> 碳排放数据概览</h2>
              <p class="module-desc">全面的碳排放数据统计与分析，实时监控全国碳排放情况</p>
            </div>

            <!-- 关键指标卡片 -->
            <div class="echarts-data-num">
              <div class="data-item">
                <dl>
                  <dt>年度碳排放总量</dt>
                  <dd>12.8 亿吨</dd>
                  <dd class="trend up">同比 +3.2%</dd>
                </dl>
                <div class="card-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" width="56" height="56" viewBox="0 0 24 24" fill="#0046DB">
                    <path d="M12 2L4 5v6.09c0 5.05 3.41 9.76 8 10.91 4.59-1.15 8-5.86 8-10.91V5l-8-3zm0 2l6 1.83-6 1.82-6-1.82L12 4zm0 7c1.65 0 3 1.35 3 3s-1.35 3-3 3-3-1.35-3-3 1.35-3 3-3z"/>
                  </svg>
                </div>
              </div>

              <div class="data-item">
                <dl>
                  <dt>累计减排量</dt>
                  <dd>2.4 亿吨</dd>
                  <dd class="trend down">同比 -15.7%</dd>
                </dl>
                <div class="card-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" width="56" height="56" viewBox="0 0 24 24" fill="#0046DB">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                  </svg>
                </div>
              </div>

              <div class="data-item">
                <dl>
                  <dt>碳强度</dt>
                  <dd>1.24 t/万元</dd>
                  <dd class="trend down">同比 -8.3%</dd>
                </dl>
                <div class="card-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" width="56" height="56" viewBox="0 0 24 24" fill="#0046DB">
                    <path d="M20 6h-8l-2-2H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V8c0-1.1-.9-2-2-2zm-5 3c1.1 0 2 .9 2 2s-.9 2-2 2-2-.9-2-2 .9-2 2-2zm4 8h-8v-1c0-1.33 2.67-2 4-2s4 .67 4 2v1z"/>
                  </svg>
                </div>
              </div>

              <div class="data-item">
                <dl>
                  <dt>覆盖企业数量</dt>
                  <dd>3,458 家</dd>
                  <dd class="trend up">同比 +12.5%</dd>
                </dl>
                <div class="card-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" width="56" height="56" viewBox="0 0 24 24" fill="#0046DB">
                    <path d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z"/>
                  </svg>
                </div>
              </div>

              <div class="data-item">
                <dl>
                  <dt>行业覆盖数</dt>
                  <dd>18 个行业</dd>
                </dl>
                <div class="card-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" width="56" height="56" viewBox="0 0 24 24" fill="#0046DB">
                    <path d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-1 9h-4v4h-2v-4H9V9h4V5h2v4h4v2z"/>
                  </svg>
                </div>
              </div>

              <div class="data-item">
                <dl>
                  <dt>数据更新时间</dt>
                  <dd>2024-Q1</dd>
                </dl>
                <div class="card-icon">
                  <svg xmlns="http://www.w3.org/2000/svg" width="56" height="56" viewBox="0 0 24 24" fill="#0046DB">
                    <path d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"/>
                  </svg>
                </div>
              </div>
            </div>
          </div>

          <!-- ==================== 行业分析模块 ==================== -->
          <div class="module-content" v-if="activeModule === 'industry'">
            <!-- 模块标题 -->
            <div class="module-header">
              <h2><i class="fas fa-industry"></i> {{ currentIndustry.name }}碳排放分析</h2>
              <p class="module-desc">{{ currentIndustry.description }}</p>
            </div>

            <!-- 行业关键指标 -->
            <div class="industry-stats">
              <div class="stat-row">
                <div class="stat-box">
                  <div class="stat-icon">
                    <i class="fas fa-smog"></i>
                  </div>
                  <div class="stat-content">
                    <div class="stat-title">行业碳排放量</div>
                    <div class="stat-value">{{ currentIndustry.totalEmission }} 万吨</div>
                    <div class="stat-change">占全国总量 {{ currentIndustry.percentage }}</div>
                  </div>
                </div>

                <div class="stat-box">
                  <div class="stat-icon">
                    <i class="fas fa-building"></i>
                  </div>
                  <div class="stat-content">
                    <div class="stat-title">企业数量</div>
                    <div class="stat-value">{{ currentIndustry.companyCount }} 家</div>
                    <div class="stat-change">重点监控企业 {{ currentIndustry.keyCompanyCount }} 家</div>
                  </div>
                </div>

                <div class="stat-box">
                  <div class="stat-icon">
                    <i class="fas fa-balance-scale"></i>
                  </div>
                  <div class="stat-content">
                    <div class="stat-title">平均碳强度</div>
                    <div class="stat-value">{{ currentIndustry.avgIntensity }} t/万元</div>
                    <div class="stat-change" :class="currentIndustry.trend > 0 ? 'up' : 'down'">
                      年度变化 {{ currentIndustry.trend > 0 ? '+' : '' }}{{ currentIndustry.trend }}%
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 行业碳排放构成 -->
            <div class="industry-composition">
              <div class="section-header">
                <h3><i class="fas fa-pie-chart"></i> 碳排放构成分析</h3>
                <p>分析{{ currentIndustry.name }}碳排放的主要来源</p>
              </div>
              <div class="composition-chart">
                <div class="mock-composition">
                  <div class="composition-item" v-for="item in currentIndustry.composition"
                       :key="item.name"
                       :style="{backgroundColor: item.color, flex: item.percentage}">
                    <span class="comp-name">{{ item.name }}</span>
                    <span class="comp-value">{{ item.percentage }}%</span>
                  </div>
                </div>
                <div class="composition-legend">
                  <div class="legend-item" v-for="item in currentIndustry.composition" :key="item.name">
                    <span class="legend-color" :style="{backgroundColor: item.color}"></span>
                    <span class="legend-text">{{ item.name }} ({{ item.percentage }}%)</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 行业排放趋势 -->
            <div class="industry-trend">
              <div class="section-header">
                <h3><i class="fas fa-chart-line"></i> 近5年排放趋势</h3>
                <p>{{ currentIndustry.name }}碳排放变化趋势分析</p>
              </div>
              <div class="trend-chart">
                <div class="mock-trend-chart">
                  <div class="trend-line">
                    <div class="trend-point" style="left: 10%; bottom: 30%"></div>
                    <div class="trend-point" style="left: 30%; bottom: 35%"></div>
                    <div class="trend-point" style="left: 50%; bottom: 40%"></div>
                    <div class="trend-point" style="left: 70%; bottom: 38%"></div>
                    <div class="trend-point" style="left: 90%; bottom: 35%"></div>
                  </div>
                  <div class="trend-year">2019</div>
                  <div class="trend-year">2020</div>
                  <div class="trend-year">2021</div>
                  <div class="trend-year">2022</div>
                  <div class="trend-year">2023</div>
                </div>
              </div>
            </div>

            <!-- 行业减排措施 -->
            <div class="reduction-measures">
              <div class="section-header">
                <h3><i class="fas fa-lightbulb"></i> 主要减排措施</h3>
                <p>{{ currentIndustry.name }}可采用的减排技术方案</p>
              </div>
              <div class="measures-grid">
                <div class="measure-card" v-for="measure in currentIndustry.measures" :key="measure.id">
                  <div class="measure-icon">
                    <i :class="measure.icon"></i>
                  </div>
                  <div class="measure-content">
                    <h4>{{ measure.title }}</h4>
                    <p>{{ measure.description }}</p>
                    <div class="measure-meta">
                      <span class="measure-effect">
                        <i class="fas fa-bullseye"></i> 减排潜力：{{ measure.potential }}
                      </span>
                      <span class="measure-cost">
                        <i class="fas fa-dollar-sign"></i> 投资成本：{{ measure.cost }}
                      </span>
                    </div>
                    <button class="btn-detail" @click="viewMeasureDetail(measure)">查看详情</button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- ==================== 区域分布模块 ==================== -->
          <div class="module-content" v-if="activeModule === 'region'">
            <div class="module-header">
              <h2><i class="fas fa-map"></i> 区域碳排放分布</h2>
              <p class="module-desc">全国各区域碳排放数据可视化分析，支持地图交互查询</p>
            </div>

            <!-- 区域选择 -->
            <div class="region-selector">
              <div class="selector-header">
                <h3><i class="fas fa-filter"></i> 区域筛选</h3>
              </div>
              <div class="selector-grid">
                <div class="region-type">
                  <label><i class="fas fa-layer-group"></i> 区域类型</label>
                  <select v-model="regionType">
                    <option value="province">省级行政区</option>
                    <option value="city">地级市</option>
                    <option value="economic">经济区域</option>
                  </select>
                </div>
                <div class="region-year">
                  <label><i class="fas fa-calendar"></i> 数据年份</label>
                  <select v-model="regionYear">
                    <option value="2023">2023年</option>
                    <option value="2022">2022年</option>
                    <option value="2021">2021年</option>
                  </select>
                </div>
                <div class="region-indicator">
                  <label><i class="fas fa-chart-bar"></i> 指标类型</label>
                  <select v-model="regionIndicator">
                    <option value="total">碳排放总量</option>
                    <option value="intensity">碳强度</option>
                    <option value="growth">增长率</option>
                  </select>
                </div>
                <div class="region-sort">
                  <label><i class="fas fa-sort"></i> 排序方式</label>
                  <select v-model="regionSort">
                    <option value="desc">从高到低</option>
                    <option value="asc">从低到高</option>
                  </select>
                </div>
              </div>
            </div>

            <!-- 地图可视化 -->
            <div class="map-visualization">
              <div class="section-header">
                <h3><i class="fas fa-map-marked-alt"></i> 碳排放地理分布图</h3>
              </div>
              <div class="map-container">
                <div class="mock-map-large">
                  <div class="map-region" v-for="region in mapRegions" :key="region.id"
                       :style="{
                         left: region.x + '%',
                         top: region.y + '%',
                         width: region.size + 'px',
                         height: region.size + 'px',
                         backgroundColor: region.color
                       }"
                       @click="viewRegionMapDetail(region)">
                    <span class="region-name">{{ region.name }}</span>
                    <span class="region-value">{{ region.value }}</span>
                  </div>
                </div>
                <div class="map-legend">
                  <div class="legend-title">碳排放量(万吨)</div>
                  <div class="legend-scale">
                    <div class="scale-item" style="background-color: #e6f7ff">0-100</div>
                    <div class="scale-item" style="background-color: #bae7ff">100-500</div>
                    <div class="scale-item" style="background-color: #91d5ff">500-1000</div>
                    <div class="scale-item" style="background-color: #69c0ff">1000-2000</div>
                    <div class="scale-item" style="background-color: #40a9ff">2000-5000</div>
                    <div class="scale-item" style="background-color: #1890ff">5000+</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 区域排名 -->
            <div class="region-ranking">
              <div class="section-header">
                <h3><i class="fas fa-trophy"></i> 区域碳排放排名</h3>
              </div>
              <div class="ranking-table">
                <table>
                  <thead>
                  <tr>
                    <th>排名</th>
                    <th>区域</th>
                    <th>碳排放量(万吨)</th>
                    <th>碳强度(t/万元)</th>
                    <th>同比变化</th>
                    <th>操作</th>
                  </tr>
                  </thead>
                  <tbody>
                  <tr v-for="(region, index) in regionRanking" :key="region.id">
                    <td>
                        <span class="rank-number" :class="{top3: index < 3}">
                          {{ index + 1 }}
                        </span>
                    </td>
                    <td>{{ region.name }}</td>
                    <td class="emission-value">{{ region.emission }}</td>
                    <td>{{ region.intensity }}</td>
                    <td>
                        <span :class="['trend-indicator', region.trend > 0 ? 'up' : 'down']">
                          {{ region.trend > 0 ? '+' : '' }}{{ region.trend }}%
                        </span>
                    </td>
                    <td>
                      <button class="btn-detail" @click="viewRegionDetail(region)">
                        <i class="fas fa-info-circle"></i> 详情
                      </button>
                    </td>
                  </tr>
                  </tbody>
                </table>
              </div>
            </div>
          </div>

          <!-- ==================== 减排技术模块 ==================== -->
          <div class="module-content" v-if="activeModule === 'technology'">
            <div class="module-header">
              <h2><i class="fas fa-cogs"></i> 碳减排技术库</h2>
              <p class="module-desc">全面的碳减排技术方案与案例，助力企业实现碳中和目标</p>
            </div>

            <!-- 技术分类 -->
            <div class="tech-categories">
              <div class="section-header">
                <h3><i class="fas fa-sitemap"></i> 技术分类</h3>
              </div>
              <div class="categories-grid">
                <div class="category-card" v-for="category in techCategories" :key="category.id"
                     :class="{active: activeTechCategory === category.id}"
                     @click="switchTechCategory(category.id)">
                  <div class="category-icon">
                    <i :class="category.icon"></i>
                  </div>
                  <div class="category-content">
                    <h4>{{ category.name }}</h4>
                    <p>{{ category.description }}</p>
                    <div class="tech-count">{{ category.count }}项技术</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 技术列表 -->
            <div class="tech-list">
              <div class="section-header">
                <h3><i class="fas fa-list"></i> 技术方案列表</h3>
                <div class="list-controls">
                  <input type="text" placeholder="搜索技术方案..." v-model="techSearch">
                  <select v-model="techSort">
                    <option value="popular">按热度</option>
                    <option value="effect">按减排效果</option>
                    <option value="cost">按投资成本</option>
                  </select>
                </div>
              </div>

              <div class="tech-grid">
                <div class="tech-card" v-for="tech in filteredTechs" :key="tech.id">
                  <div class="tech-header">
                    <h4>{{ tech.name }}</h4>
                    <span class="tech-tag" :style="{backgroundColor: tech.tagColor}">
                      {{ tech.category }}
                    </span>
                  </div>
                  <div class="tech-content">
                    <p>{{ tech.description }}</p>
                    <div class="tech-metrics">
                      <div class="metric">
                        <i class="fas fa-leaf"></i>
                        <span>减排效果：{{ tech.reduction }}%</span>
                      </div>
                      <div class="metric">
                        <i class="fas fa-dollar-sign"></i>
                        <span>投资成本：{{ tech.investment }}</span>
                      </div>
                      <div class="metric">
                        <i class="fas fa-clock"></i>
                        <span>回收期：{{ tech.payback }}</span>
                      </div>
                    </div>
                    <div class="tech-applications">
                      <div class="app-title">适用行业：</div>
                      <div class="app-tags">
                        <span class="app-tag" v-for="industry in tech.industries" :key="industry">
                          {{ industry }}
                        </span>
                      </div>
                    </div>
                  </div>
                  <div class="tech-footer">
                    <button class="btn-detail" @click="viewTechDetail(tech)">
                      <i class="fas fa-info-circle"></i> 查看详情
                    </button>
                    <button class="btn-case" @click="viewTechCases(tech)">
                      <i class="fas fa-briefcase"></i> 案例研究
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- ==================== 政策法规模块 ==================== -->
          <div class="module-content" v-if="activeModule === 'policy'">
            <div class="module-header">
              <h2><i class="fas fa-file-contract"></i> 政策法规库</h2>
              <p class="module-desc">国内外碳排放相关政策法规，及时更新政策动态</p>
            </div>

            <!-- 政策分类 -->
            <div class="policy-categories">
              <div class="section-header">
                <h3><i class="fas fa-filter"></i> 政策分类</h3>
              </div>
              <div class="category-tabs">
                <div class="tab-item"
                     v-for="category in policyCategories"
                     :key="category.id"
                     :class="{active: activePolicyCategory === category.id}"
                     @click="switchPolicyCategory(category.id)">
                  {{ category.name }}
                  <span class="tab-count">{{ category.count }}</span>
                </div>
              </div>
            </div>

            <!-- 政策列表 -->
            <div class="policy-list">
              <div class="section-header">
                <h3><i class="fas fa-newspaper"></i> 政策法规列表</h3>
                <div class="list-controls">
                  <input type="text" placeholder="搜索政策法规..." v-model="policySearch">
                  <select v-model="policySort">
                    <option value="date">按发布时间</option>
                    <option value="level">按效力级别</option>
                  </select>
                </div>
              </div>

              <div class="policy-grid">
                <div class="policy-card" v-for="policy in filteredPolicies" :key="policy.id">
                  <div class="policy-header">
                    <div class="policy-title">
                      <h4>{{ policy.title }}</h4>
                      <span class="policy-level" :class="policy.level">
                        {{ policy.levelText }}
                      </span>
                    </div>
                    <div class="policy-meta">
                      <span class="meta-item">
                        <i class="fas fa-calendar"></i> {{ policy.date }}
                      </span>
                      <span class="meta-item">
                        <i class="fas fa-building"></i> {{ policy.agency }}
                      </span>
                      <span class="meta-item">
                        <i class="fas fa-tag"></i> {{ policy.category }}
                      </span>
                    </div>
                  </div>
                  <div class="policy-content">
                    <p>{{ policy.description }}</p>
                    <div class="policy-keywords">
                      <span class="keyword" v-for="keyword in policy.keywords" :key="keyword">
                        {{ keyword }}
                      </span>
                    </div>
                  </div>
                  <div class="policy-footer">
                    <button class="btn-detail" @click="viewPolicyDetail(policy)">
                      <i class="fas fa-info-circle"></i> 政策解读
                    </button>
                    <button class="btn-download" @click="downloadPolicy(policy)">
                      <i class="fas fa-download"></i> 下载原文
                    </button>
                    <button class="btn-share" @click="sharePolicy(policy)">
                      <i class="fas fa-share"></i> 分享
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- 政策动态 -->
            <div class="policy-news">
              <div class="section-header">
                <h3><i class="fas fa-bullhorn"></i> 政策动态</h3>
              </div>
              <div class="news-list">
                <div class="news-item" v-for="news in policyNews" :key="news.id">
                  <div class="news-date">{{ news.date }}</div>
                  <div class="news-content">
                    <div class="news-title">{{ news.title }}</div>
                    <div class="news-desc">{{ news.description }}</div>
                  </div>
                  <button class="btn-news" @click="viewNewsDetail(news)">
                    查看详情
                  </button>
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
  name: "CarbonEmission",
  components: {
    Header,
    Footer,
  },
  data() {
    return {
      // 模块管理
      activeModule: 'overview',
      activeIndustry: 'steel',
      isIndustryMenuExpanded: false, // 新增：控制行业子菜单展开状态

      // 行业数据
      industryList: [
        { id: 'steel', name: '钢铁行业' },
        { id: 'nonferrous', name: '有色金属' },
        { id: 'chemical', name: '化工行业' },
        { id: 'power', name: '电力行业' },
        { id: 'building', name: '建材行业' },
        { id: 'transport', name: '交通运输' },
        { id: 'agriculture', name: '农业' },
        { id: 'others', name: '其他行业' }
      ],

      // 当前行业数据
      currentIndustry: {},

      // 区域分布数据
      regionType: 'province',
      regionYear: '2023',
      regionIndicator: 'total',
      regionSort: 'desc',

      mapRegions: [
        { id: 1, name: '河北', value: '5200', x: 40, y: 25, size: 70, color: '#1890ff' },
        { id: 2, name: '江苏', value: '4800', x: 50, y: 30, size: 65, color: '#40a9ff' },
        { id: 3, name: '山东', value: '4500', x: 45, y: 28, size: 60, color: '#69c0ff' },
        { id: 4, name: '广东', value: '4200', x: 35, y: 45, size: 55, color: '#91d5ff' },
        { id: 5, name: '浙江', value: '3800', x: 55, y: 35, size: 50, color: '#bae7ff' },
        { id: 6, name: '河南', value: '3500', x: 42, y: 32, size: 45, color: '#e6f7ff' },
        { id: 7, name: '辽宁', value: '3200', x: 52, y: 20, size: 40, color: '#e6f7ff' },
        { id: 8, name: '四川', value: '3000', x: 30, y: 38, size: 35, color: '#bae7ff' }
      ],

      regionRanking: [
        { id: 1, name: '河北省', emission: '5,200', intensity: '2.8', trend: -10.5 },
        { id: 2, name: '江苏省', emission: '4,800', intensity: '2.1', trend: -8.3 },
        { id: 3, name: '山东省', emission: '4,500', intensity: '2.5', trend: -9.1 },
        { id: 4, name: '广东省', emission: '4,200', intensity: '1.8', trend: -7.6 },
        { id: 5, name: '浙江省', emission: '3,800', intensity: '1.6', trend: -6.9 },
        { id: 6, name: '河南省', emission: '3,500', intensity: '2.3', trend: -8.8 },
        { id: 7, name: '辽宁省', emission: '3,200', intensity: '3.1', trend: -11.2 },
        { id: 8, name: '四川省', emission: '3,000', intensity: '2.0', trend: -5.4 }
      ],

      // 减排技术数据
      activeTechCategory: 'all',
      techSearch: '',
      techSort: 'popular',

      techCategories: [
        { id: 'all', name: '全部技术', icon: 'fas fa-boxes', description: '所有减排技术方案', count: 156 },
        { id: 'energy', name: '节能技术', icon: 'fas fa-bolt', description: '提高能源利用效率', count: 45 },
        { id: 'renewable', name: '可再生能源', icon: 'fas fa-sun', description: '太阳能、风能等清洁能源', count: 38 },
        { id: 'ccus', name: 'CCUS技术', icon: 'fas fa-industry', description: '碳捕集利用与封存', count: 25 },
        { id: 'process', name: '工艺优化', icon: 'fas fa-cogs', description: '生产过程优化改进', count: 32 },
        { id: 'circular', name: '循环利用', icon: 'fas fa-recycle', description: '资源循环利用技术', count: 26 }
      ],

      // 政策法规数据
      activePolicyCategory: 'national',
      policySearch: '',
      policySort: 'date',

      policyCategories: [
        { id: 'national', name: '国家政策', count: 156 },
        { id: 'local', name: '地方政策', count: 342 },
        { id: 'standard', name: '行业标准', count: 89 },
        { id: 'international', name: '国际公约', count: 45 },
        { id: 'guideline', name: '技术指南', count: 67 }
      ],
    };
  },
  computed: {
    // 计算过滤后的技术列表
    filteredTechs() {
      // 这里应该根据实际数据过滤，暂时返回模拟数据
      return [
        {
          id: 1,
          name: '高炉煤气余压发电技术',
          category: '节能技术',
          tagColor: '#0046DB',
          description: '利用高炉煤气余压进行发电，提高能源利用效率',
          reduction: 15,
          investment: '中等',
          payback: '2-3年',
          industries: ['钢铁', '冶金']
        },
        {
          id: 2,
          name: '光伏发电系统',
          category: '可再生能源',
          tagColor: '#00B4FF',
          description: '利用太阳能光伏板发电，替代传统化石能源',
          reduction: 100,
          investment: '较高',
          payback: '4-6年',
          industries: ['电力', '制造业', '建筑业']
        },
        {
          id: 3,
          name: '碳捕集与封存技术',
          category: 'CCUS技术',
          tagColor: '#FF6B6B',
          description: '捕集工业排放的二氧化碳并进行安全封存',
          reduction: 85,
          investment: '很高',
          payback: '8-10年',
          industries: ['电力', '化工', '水泥']
        },
        {
          id: 4,
          name: '高效电机系统',
          category: '节能技术',
          tagColor: '#0046DB',
          description: '采用高效电机和变频控制，降低电力消耗',
          reduction: 20,
          investment: '较低',
          payback: '1-2年',
          industries: ['制造业', '矿业', '化纤']
        }
      ];
    },

    // 计算过滤后的政策列表
    filteredPolicies() {
      return [
        {
          id: 1,
          title: '《2030年前碳达峰行动方案》',
          level: 'national',
          levelText: '国家政策',
          date: '2021-10-26',
          agency: '国务院',
          category: '行动方案',
          description: '明确2030年前实现碳达峰的总体目标和重点任务',
          keywords: ['碳达峰', '行动方案', '2030年']
        },
        {
          id: 2,
          title: '《企业温室气体排放核算与报告指南》',
          level: 'standard',
          levelText: '国家标准',
          date: '2022-03-15',
          agency: '生态环境部',
          category: '核算标准',
          description: '规范企业温室气体排放核算方法与报告要求',
          keywords: ['核算方法', '报告指南', '温室气体']
        }
      ];
    },

    // 政策动态
    policyNews() {
      return [
        {
          id: 1,
          date: '2024-03-20',
          title: '全国碳市场成交量创新高',
          description: '本月碳配额成交量突破1000万吨，交易活跃度显著提升'
        },
        {
          id: 2,
          date: '2024-03-18',
          title: '钢铁行业碳排放标准更新',
          description: '新版标准将于4月1日起实施，要求更加严格'
        }
      ];
    }
  },
  created() {
    this.switchIndustry('steel');
  },
  methods: {
    // 切换主模块
    switchModule(module) {
      // 如果点击的是行业模块
      if (module === 'industry') {
        if (this.activeModule === 'industry') {
          // 如果已经激活，则切换子菜单展开状态
          this.isIndustryMenuExpanded = !this.isIndustryMenuExpanded;
        } else {
          // 如果未激活，则激活并展开子菜单
          this.activeModule = module;
          this.isIndustryMenuExpanded = false;
          this.switchIndustry('steel');
        }
      } else {
        // 其他模块正常切换
        this.activeModule = module;
        this.isIndustryMenuExpanded = false; // 收起行业子菜单
      }
    },

    // 切换行业
    switchIndustry(industryId) {
      this.activeIndustry = industryId;
      // 保持子菜单展开状态
      this.isIndustryMenuExpanded = true;

      const industryData = {
        steel: {
          name: '钢铁行业',
          description: '钢铁行业是中国最大的碳排放行业之一，包括炼铁、炼钢、轧钢等生产过程。碳排放主要来源于化石燃料燃烧和还原反应。',
          totalEmission: '5,800',
          percentage: '45.3%',
          companyCount: '1,234',
          keyCompanyCount: '156',
          avgIntensity: '2.8',
          trend: -12.5,
          composition: [
            { name: '炼铁过程', percentage: 45, color: '#0046DB' },
            { name: '炼钢过程', percentage: 35, color: '#0080FF' },
            { name: '轧钢过程', percentage: 15, color: '#00B4FF' },
            { name: '辅助工序', percentage: 5, color: '#80D0FF' }
          ],
          measures: [
            {
              id: 1,
              title: '高炉煤气余压发电',
              description: '利用高炉煤气余压驱动透平发电，提高能源利用效率',
              potential: '15-20%',
              cost: '中等',
              icon: 'fas fa-bolt'
            },
            {
              id: 2,
              title: '转炉煤气回收利用',
              description: '转炉煤气干法除尘及回收利用技术，减少能源浪费',
              potential: '8-12%',
              cost: '较低',
              icon: 'fas fa-recycle'
            },
            {
              id: 3,
              title: '余热余压综合利用',
              description: '利用生产过程中的余热余压进行发电和供暖',
              potential: '10-15%',
              cost: '中等',
              icon: 'fas fa-fire'
            },
            {
              id: 4,
              title: '氢冶金技术应用',
              description: '使用氢气替代煤炭进行还原反应，大幅降低碳排放',
              potential: '30-50%',
              cost: '很高',
              icon: 'fas fa-atom'
            }
          ]
        },
        power: {
          name: '电力行业',
          description: '电力行业是中国碳排放的主要来源，以燃煤发电为主。近年来新能源发电占比逐步提升，碳排放强度持续下降。',
          totalEmission: '4,200',
          percentage: '32.8%',
          companyCount: '5,678',
          keyCompanyCount: '1,023',
          avgIntensity: '4.1',
          trend: 2.3,
          composition: [
            { name: '燃煤发电', percentage: 60, color: '#FF6B6B' },
            { name: '燃气发电', percentage: 25, color: '#4ECDC4' },
            { name: '水力发电', percentage: 10, color: '#45B7D1' },
            { name: '其他新能源', percentage: 5, color: '#96CEB4' }
          ],
          measures: [
            {
              id: 1,
              title: '超超临界发电技术',
              description: '提高燃煤发电效率，降低单位发电煤耗',
              potential: '10-15%',
              cost: '较高',
              icon: 'fas fa-tachometer-alt'
            },
            {
              id: 2,
              title: '碳捕集与封存',
              description: '捕集电厂排放的二氧化碳并进行安全封存',
              potential: '80-90%',
              cost: '很高',
              icon: 'fas fa-industry'
            },
            {
              id: 3,
              title: '大规模光伏发电',
              description: '建设大型光伏电站，替代传统火电',
              potential: '100%',
              cost: '中等',
              icon: 'fas fa-sun'
            },
            {
              id: 4,
              title: '风力发电替代',
              description: '风力发电技术应用，减少化石能源依赖',
              potential: '100%',
              cost: '中等',
              icon: 'fas fa-wind'
            }
          ]
        },
        chemical: {
          name: '化工行业',
          description: '化工行业是重要的碳排放行业，主要包括化肥、石化、基础化工等子行业。碳排放主要来自燃料燃烧和工艺过程。',
          totalEmission: '1,900',
          percentage: '14.8%',
          companyCount: '3,450',
          keyCompanyCount: '456',
          avgIntensity: '2.9',
          trend: -7.8,
          composition: [
            { name: '化肥生产', percentage: 40, color: '#FF6B6B' },
            { name: '石化过程', percentage: 35, color: '#4ECDC4' },
            { name: '基础化工', percentage: 20, color: '#45B7D1' },
            { name: '其他化工', percentage: 5, color: '#96CEB4' }
          ],
          measures: [
            {
              id: 1,
              title: '工艺过程优化',
              description: '优化化工反应过程，提高原料转化率',
              potential: '10-15%',
              cost: '中等',
              icon: 'fas fa-cogs'
            },
            {
              id: 2,
              title: '余热回收利用',
              description: '回收化工生产过程中的余热用于发电或供暖',
              potential: '8-12%',
              cost: '较低',
              icon: 'fas fa-fire'
            },
            {
              id: 3,
              title: '原料替代技术',
              description: '使用生物质等可再生原料替代化石原料',
              potential: '20-30%',
              cost: '较高',
              icon: 'fas fa-leaf'
            },
            {
              id: 4,
              title: '催化剂优化',
              description: '采用高效催化剂降低反应温度和能耗',
              potential: '5-10%',
              cost: '较低',
              icon: 'fas fa-flask'
            }
          ]
        },
        building: {
          name: '建材行业',
          description: '建材行业主要包括水泥、玻璃、陶瓷等生产，碳排放主要来自原料煅烧和燃料燃烧过程。',
          totalEmission: '1,100',
          percentage: '8.6%',
          companyCount: '2,780',
          keyCompanyCount: '320',
          avgIntensity: '3.5',
          trend: -10.2,
          composition: [
            { name: '水泥生产', percentage: 70, color: '#FF6B6B' },
            { name: '玻璃生产', percentage: 15, color: '#4ECDC4' },
            { name: '陶瓷生产', percentage: 10, color: '#45B7D1' },
            { name: '其他建材', percentage: 5, color: '#96CEB4' }
          ],
          measures: [
            {
              id: 1,
              title: '新型干法水泥技术',
              description: '采用新型干法生产工艺，降低能耗',
              potential: '15-20%',
              cost: '较高',
              icon: 'fas fa-industry'
            },
            {
              id: 2,
              title: '替代燃料应用',
              description: '使用生物质燃料替代煤炭',
              potential: '10-15%',
              cost: '中等',
              icon: 'fas fa-leaf'
            },
            {
              id: 3,
              title: '余热发电技术',
              description: '利用窑炉余热进行发电',
              potential: '8-12%',
              cost: '中等',
              icon: 'fas fa-bolt'
            },
            {
              id: 4,
              title: '原料替代技术',
              description: '使用工业废渣替代部分原料',
              potential: '5-10%',
              cost: '较低',
              icon: 'fas fa-recycle'
            }
          ]
        },
        nonferrous: {
          name: '有色金属',
          description: '有色金属行业包括铝、铜、铅、锌等金属冶炼，碳排放主要来自电解过程和燃料燃烧。',
          totalEmission: '800',
          percentage: '6.3%',
          companyCount: '1,890',
          keyCompanyCount: '245',
          avgIntensity: '3.2',
          trend: -5.6,
          composition: [
            { name: '铝冶炼', percentage: 60, color: '#FF6B6B' },
            { name: '铜冶炼', percentage: 25, color: '#4ECDC4' },
            { name: '其他金属', percentage: 15, color: '#45B7D1' }
          ],
          measures: [
            {
              id: 1,
              title: '电解槽优化技术',
              description: '优化电解槽结构，降低电解能耗',
              potential: '8-12%',
              cost: '中等',
              icon: 'fas fa-bolt'
            },
            {
              id: 2,
              title: '余热回收利用',
              description: '回收冶炼过程余热用于发电',
              potential: '6-10%',
              cost: '较低',
              icon: 'fas fa-fire'
            },
            {
              id: 3,
              title: '再生金属利用',
              description: '提高再生金属使用比例',
              potential: '30-40%',
              cost: '中等',
              icon: 'fas fa-recycle'
            },
            {
              id: 4,
              title: '工艺过程优化',
              description: '优化冶炼工艺参数',
              potential: '5-8%',
              cost: '较低',
              icon: 'fas fa-cogs'
            }
          ]
        },
        transport: {
          name: '交通运输',
          description: '交通运输行业包括公路、铁路、航空、水运等，碳排放主要来自化石燃料燃烧。',
          totalEmission: '600',
          percentage: '4.7%',
          companyCount: '5,670',
          keyCompanyCount: '890',
          avgIntensity: '1.8',
          trend: 5.2,
          composition: [
            { name: '公路运输', percentage: 70, color: '#FF6B6B' },
            { name: '航空运输', percentage: 15, color: '#4ECDC4' },
            { name: '水路运输', percentage: 10, color: '#45B7D1' },
            { name: '铁路运输', percentage: 5, color: '#96CEB4' }
          ],
          measures: [
            {
              id: 1,
              title: '新能源汽车推广',
              description: '推广电动汽车、氢燃料电池汽车',
              potential: '30-50%',
              cost: '较高',
              icon: 'fas fa-car'
            },
            {
              id: 2,
              title: '能效提升技术',
              description: '提高运输工具能效',
              potential: '10-15%',
              cost: '中等',
              icon: 'fas fa-tachometer-alt'
            },
            {
              id: 3,
              title: '多式联运优化',
              description: '优化运输结构，发展多式联运',
              potential: '8-12%',
              cost: '较低',
              icon: 'fas fa-train'
            },
            {
              id: 4,
              title: '替代燃料应用',
              description: '使用生物燃料、LNG等替代燃料',
              potential: '15-20%',
              cost: '中等',
              icon: 'fas fa-gas-pump'
            }
          ]
        },
        agriculture: {
          name: '农业',
          description: '农业碳排放主要来自农业生产活动，包括农田管理、畜牧业、渔业等。',
          totalEmission: '300',
          percentage: '2.3%',
          companyCount: '12,450',
          keyCompanyCount: '1,560',
          avgIntensity: '0.9',
          trend: -3.1,
          composition: [
            { name: '种植业', percentage: 45, color: '#FF6B6B' },
            { name: '畜牧业', percentage: 40, color: '#4ECDC4' },
            { name: '渔业', percentage: 10, color: '#45B7D1' },
            { name: '其他农业', percentage: 5, color: '#96CEB4' }
          ],
          measures: [
            {
              id: 1,
              title: '精准农业技术',
              description: '应用精准农业技术减少化肥农药使用',
              potential: '10-15%',
              cost: '中等',
              icon: 'fas fa-tractor'
            },
            {
              id: 2,
              title: '秸秆综合利用',
              description: '秸秆还田、能源化利用等技术',
              potential: '8-12%',
              cost: '较低',
              icon: 'fas fa-recycle'
            },
            {
              id: 3,
              title: '畜禽粪污处理',
              description: '畜禽粪污资源化利用技术',
              potential: '15-20%',
              cost: '中等',
              icon: 'fas fa-paw'
            },
            {
              id: 4,
              title: '生态农业模式',
              description: '发展生态循环农业',
              potential: '10-15%',
              cost: '较低',
              icon: 'fas fa-leaf'
            }
          ]
        },
        others: {
          name: '其他行业',
          description: '包括服务业、建筑业、轻工业等其他行业的碳排放。',
          totalEmission: '200',
          percentage: '1.6%',
          companyCount: '8,900',
          keyCompanyCount: '1,120',
          avgIntensity: '1.2',
          trend: 1.8,
          composition: [
            { name: '服务业', percentage: 50, color: '#FF6B6B' },
            { name: '建筑业', percentage: 30, color: '#4ECDC4' },
            { name: '轻工业', percentage: 20, color: '#45B7D1' }
          ],
          measures: [
            {
              id: 1,
              title: '建筑节能技术',
              description: '推广绿色建筑和节能改造',
              potential: '20-30%',
              cost: '中等',
              icon: 'fas fa-building'
            },
            {
              id: 2,
              title: '能源管理系统',
              description: '建立能源管理体系',
              potential: '10-15%',
              cost: '较低',
              icon: 'fas fa-chart-line'
            },
            {
              id: 3,
              title: '设备能效提升',
              description: '更新高效节能设备',
              potential: '8-12%',
              cost: '中等',
              icon: 'fas fa-cog'
            },
            {
              id: 4,
              title: '可再生能源应用',
              description: '应用太阳能、地热能等',
              potential: '15-25%',
              cost: '较高',
              icon: 'fas fa-sun'
            }
          ]
        }
      };

      this.currentIndustry = industryData[industryId] || industryData.steel;
    },

    // 切换技术分类
    switchTechCategory(categoryId) {
      this.activeTechCategory = categoryId;
    },

    // 切换政策分类
    switchPolicyCategory(categoryId) {
      this.activePolicyCategory = categoryId;
    },

    // 导出数据
    exportOverviewData() {
      alert('数据导出功能正在开发中...');
    },

    // 查看详情
    viewIndustryDetail(item) {
      // 跳转到对应的行业分析
      this.switchModule('industry');
      this.switchIndustry(this.getIndustryIdByName(item.name));
    },

    getIndustryIdByName(name) {
      const nameMap = {
        '钢铁行业': 'steel',
        '电力行业': 'power',
        '化工行业': 'chemical',
        '建材行业': 'building',
        '有色金属': 'nonferrous',
        '交通运输': 'transport',
        '农业': 'agriculture',
        '其他行业': 'others'
      };
      return nameMap[name] || 'steel';
    },

    viewRegionDetail(region) {
      alert(`查看区域详情：${region.name}\n碳排放量：${region.emission}万吨\n碳强度：${region.intensity}`);
    },

    viewRegionMapDetail(region) {
      alert(`查看地图区域详情：${region.name}\n碳排放量：${region.value}万吨`);
    },

    viewTechDetail(tech) {
      alert(`查看技术详情：${tech.name}\n减排效果：${tech.reduction}%\n投资成本：${tech.investment}`);
    },

    viewTechCases(tech) {
      alert(`查看技术案例：${tech.name}\n正在加载相关案例研究...`);
    },

    viewPolicyDetail(policy) {
      alert(`查看政策详情：${policy.title}\n发布单位：${policy.agency}\n发布日期：${policy.date}`);
    },

    viewMeasureDetail(measure) {
      alert(`查看减排措施详情：${measure.title}\n减排潜力：${measure.potential}\n投资成本：${measure.cost}`);
    },

    // 其他功能
    downloadPolicy(policy) {
      alert(`下载政策文件：${policy.title}\n文件正在下载中...`);
    },

    sharePolicy(policy) {
      if (navigator.share) {
        navigator.share({
          title: policy.title,
          text: policy.description,
          url: window.location.href
        });
      } else {
        alert(`分享政策：${policy.title}\n链接已复制到剪贴板`);
      }
    },

    viewNewsDetail(news) {
      alert(`查看新闻详情：${news.title}\n发布时间：${news.date}\n${news.description}`);
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
.carbon-emission {
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
  padding: 50px 0 30px;
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

.card-icon svg {
  width: 40px;
  height: 40px;
  opacity: 0.8;
  transition: opacity 0.3s;
}

.data-item:hover .card-icon svg {
  opacity: 1;
}

/* ==================== 行业分析模块样式 ==================== */
/* 行业统计 */
.industry-stats {
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

/* 行业构成 */
.industry-composition {
  margin-bottom: 25px;
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

.composition-chart {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
}

.mock-composition {
  display: flex;
  height: 50px;
  border-radius: 25px;
  overflow: hidden;
  margin-bottom: 15px;
}

.composition-item {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 12px;
  position: relative;
  padding: 0 12px;
  transition: flex 0.3s;
}

.composition-item:hover {
  opacity: 0.9;
}

.comp-name {
  margin-right: 6px;
  font-weight: 500;
}

.comp-value {
  font-weight: 700;
}

.composition-legend {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 6px;
}

.legend-color {
  width: 10px;
  height: 10px;
  border-radius: 2px;
}

.legend-text {
  font-size: 12px;
  color: #666;
}

/* 行业趋势 */
.industry-trend {
  margin-bottom: 25px;
}

.trend-chart {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
  height: 250px;
  position: relative;
}

.mock-trend-chart {
  width: 100%;
  height: 100%;
  position: relative;
}

.trend-line {
  position: absolute;
  bottom: 40px;
  left: 40px;
  right: 40px;
  height: 2px;
  background: #0046DB;
}

.trend-point {
  position: absolute;
  width: 10px;
  height: 10px;
  background: #0046DB;
  border-radius: 50%;
  border: 2px solid #fff;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  transform: translate(-50%, 50%);
}

.trend-year {
  position: absolute;
  bottom: 15px;
  font-size: 11px;
  color: #666;
  text-align: center;
  width: 20%;
}

.trend-year:nth-child(1) { left: 0; }
.trend-year:nth-child(2) { left: 20%; }
.trend-year:nth-child(3) { left: 40%; }
.trend-year:nth-child(4) { left: 60%; }
.trend-year:nth-child(5) { left: 80%; }

/* 减排措施 */
.reduction-measures {
  margin-bottom: 0;
}

.measures-grid {
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

.measure-content {
  flex: 1;
}

.measure-card h4 {
  font-size: 16px;
  color: #333;
  margin: 0 0 8px 0;
}

.measure-card p {
  font-size: 13px;
  color: #666;
  line-height: 1.5;
  margin: 0 0 12px 0;
}

.measure-meta {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

.measure-effect,
.measure-cost {
  font-size: 12px;
  color: #666;
  display: flex;
  align-items: center;
  gap: 4px;
}

.measure-effect i,
.measure-cost i {
  color: #0046DB;
}

/* ==================== 其他模块样式 ==================== */
/* 区域选择器 */
.region-selector {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  margin-bottom: 12px;
  border: 1px solid #f0f0f0;
}

.selector-header {
  margin-bottom: 15px;
}

.selector-header h3 {
  font-size: 16px;
  color: #333;
  margin: 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.selector-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.region-type,
.region-year,
.region-indicator,
.region-sort {
  display: flex;
  flex-direction: column;
}

.region-type label,
.region-year label,
.region-indicator label,
.region-sort label {
  font-size: 13px;
  color: #666;
  margin-bottom: 6px;
  display: flex;
  align-items: center;
  gap: 5px;
}

.region-type select,
.region-year select,
.region-indicator select,
.region-sort select {
  padding: 7px 10px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  font-size: 13px;
  color: #606266;
  background: #fff;
  cursor: pointer;
}

/* 地图可视化 */
.map-visualization {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  margin-bottom: 12px;
  border: 1px solid #f0f0f0;
}

.map-container {
  position: relative;
  height: 350px;
  background: #fafafa;
  border-radius: 6px;
  overflow: hidden;
}

.mock-map-large {
  width: 100%;
  height: 100%;
  position: relative;
  background: #e6f7ff;
}

.map-region {
  position: absolute;
  border: 2px solid #fff;
  border-radius: 50%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #333;
  font-weight: 500;
  box-shadow: 0 2px 6px rgba(0,0,0,0.1);
  transform: translate(-50%, -50%);
  transition: all 0.3s;
  cursor: pointer;
}

.map-region:hover {
  transform: translate(-50%, -50%) scale(1.08);
  z-index: 10;
}

.region-name {
  font-size: 11px;
  font-weight: 600;
}

.region-value {
  font-size: 9px;
  color: #666;
}

.map-legend {
  position: absolute;
  bottom: 15px;
  right: 15px;
  background: rgba(255, 255, 255, 0.9);
  padding: 12px;
  border-radius: 6px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.1);
}

.legend-title {
  font-size: 12px;
  font-weight: 600;
  color: #333;
  margin-bottom: 8px;
}

.legend-scale {
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.scale-item {
  padding: 3px 6px;
  font-size: 11px;
  color: #333;
  border-radius: 3px;
}

/* 区域排名 */
.region-ranking {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
}

.ranking-table {
  overflow-x: auto;
}

.ranking-table table {
  width: 100%;
  border-collapse: collapse;
  min-width: 800px;
}

.ranking-table th {
  padding: 14px;
  text-align: left;
  background: #fafafa;
  color: #666;
  font-weight: 500;
  font-size: 13px;
  border-bottom: 1px solid #e8e8e8;
}

.ranking-table td {
  padding: 12px;
  color: #333;
  font-size: 13px;
  border-bottom: 1px solid #e8e8e8;
}

.rank-number {
  display: inline-block;
  width: 22px;
  height: 22px;
  background: #f0f0f0;
  border-radius: 50%;
  text-align: center;
  line-height: 22px;
  font-weight: 600;
  color: #666;
}

.rank-number.top3 {
  background: #0046DB;
  color: #fff;
}

.rank-number.top3:nth-child(1) { background: #FF6B6B; }
.rank-number.top3:nth-child(2) { background: #FFA726; }
.rank-number.top3:nth-child(3) { background: #4CAF50; }

/* 技术分类 */
.tech-categories {
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

.tech-count {
  font-size: 11px;
  color: #0046DB;
  font-weight: 600;
}

/* 技术列表 */
.tech-list {
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

.tech-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;
  margin-top: 15px;
}

.tech-card {
  background: #fff;
  border-radius: 6px;
  padding: 15px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
  transition: all 0.3s;
}

.tech-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #0046DB;
}

.tech-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 10px;
}

.tech-header h4 {
  font-size: 15px;
  color: #333;
  margin: 0;
  flex: 1;
}

.tech-tag {
  font-size: 10px;
  color: #fff;
  padding: 2px 6px;
  border-radius: 8px;
  font-weight: 500;
}

.tech-content p {
  font-size: 13px;
  color: #666;
  line-height: 1.5;
  margin: 0 0 10px 0;
}

.tech-metrics {
  display: flex;
  gap: 8px;
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

.tech-applications {
  margin-bottom: 10px;
}

.app-title {
  font-size: 12px;
  color: #666;
  margin-bottom: 4px;
}

.app-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.app-tag {
  font-size: 10px;
  color: #0046DB;
  background: rgba(0, 70, 219, 0.1);
  padding: 2px 5px;
  border-radius: 3px;
}

.tech-footer {
  display: flex;
  gap: 8px;
}

.btn-case {
  padding: 5px 10px;
  background: transparent;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  color: #666;
  font-size: 11px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.3s;
}

.btn-case:hover {
  color: #00B4FF;
  border-color: #00B4FF;
  background: rgba(0, 180, 255, 0.05);
}

/* 政策分类 */
.policy-categories {
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

/* 政策列表 */
.policy-list {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  margin-bottom: 12px;
  border: 1px solid #f0f0f0;
}

.policy-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-top: 15px;
}

.policy-card {
  background: #fff;
  border-radius: 6px;
  padding: 15px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
  transition: all 0.3s;
}

.policy-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  border-color: #0046DB;
}

.policy-header {
  margin-bottom: 10px;
}

.policy-title {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 6px;
}

.policy-title h4 {
  font-size: 15px;
  color: #333;
  margin: 0;
  flex: 1;
}

.policy-level {
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 3px;
  font-weight: 500;
  margin-left: 8px;
}

.policy-level.national {
  background: #FF6B6B;
  color: #fff;
}

.policy-level.standard {
  background: #4CAF50;
  color: #fff;
}

.policy-meta {
  display: flex;
  gap: 8px;
  font-size: 11px;
  color: #999;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 3px;
}

.policy-content p {
  font-size: 13px;
  color: #666;
  line-height: 1.5;
  margin: 0 0 10px 0;
}

.policy-keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.keyword {
  font-size: 10px;
  color: #0046DB;
  background: rgba(0, 70, 219, 0.1);
  padding: 2px 5px;
  border-radius: 3px;
}

.policy-footer {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.btn-download {
  padding: 5px 10px;
  background: transparent;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  color: #666;
  font-size: 11px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.3s;
}

.btn-download:hover {
  color: #4CAF50;
  border-color: #4CAF50;
  background: rgba(76, 175, 80, 0.05);
}

.btn-share {
  padding: 5px 10px;
  background: transparent;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  color: #666;
  font-size: 11px;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 4px;
  transition: all 0.3s;
}

.btn-share:hover {
  color: #FF6B6B;
  border-color: #FF6B6B;
  background: rgba(255, 107, 107, 0.05);
}

/* 政策动态 */
.policy-news {
  background: #fff;
  border-radius: 10px;
  padding: 18px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
}

.news-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.news-item {
  display: flex;
  align-items: flex-start;
  padding: 10px;
  background: #f8f9fa;
  border-radius: 6px;
  transition: all 0.3s;
}

.news-item:hover {
  background: #e6f7ff;
}

.news-date {
  width: 70px;
  flex-shrink: 0;
  font-size: 11px;
  color: #999;
  line-height: 1.4;
}

.news-content {
  flex: 1;
}

.news-title {
  font-size: 13px;
  color: #333;
  margin-bottom: 3px;
  font-weight: 500;
}

.news-desc {
  font-size: 11px;
  color: #666;
  line-height: 1.4;
}

.btn-news {
  padding: 5px 10px;
  background: transparent;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  color: #666;
  font-size: 11px;
  cursor: pointer;
  margin-left: 8px;
  transition: all 0.3s;
}

.btn-news:hover {
  color: #0046DB;
  border-color: #0046DB;
  background: rgba(0, 70, 219, 0.05);
}

/* ==================== 响应式设计 ==================== */
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

  .measures-grid {
    grid-template-columns: 1fr;
  }

  .categories-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .tech-grid {
    grid-template-columns: 1fr;
  }

  .selector-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 992px) {
  /* 移动端改为单列布局 */
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

  /* 参考Search.vue的响应式设计 */
  .carbon-emission {
    padding-top: 80px; /* 参考Search.vue在1600px以下的padding-top: 80px */
  }
}

@media (max-width: 1000px) {
  /* 参考Search.vue在1000px以下的响应式设计 */
  .carbon-emission {
    padding-top: 30px; /* 参考Search.vue在1000px以下的padding-top: 30px */
  }

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

  .selector-grid {
    grid-template-columns: 1fr;
  }

  .measures-grid {
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

  .selector-grid {
    grid-template-columns: 1fr;
  }

  .measures-grid {
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

  .policy-footer,
  .tech-footer {
    flex-wrap: wrap;
  }

  .btn-detail,
  .btn-case,
  .btn-download,
  .btn-share {
    flex: 1;
    min-width: 90px;
    justify-content: center;
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
.chart-container,
.stat-box,
.measure-card,
.tech-card,
.policy-card {
  animation: fadeIn 0.3s ease-out;
}
</style>