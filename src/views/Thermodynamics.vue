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

            <!-- 模型工具 -->
            <dl class="data-aggregation-nav"
                :class="{active: activeCategory === 'features'}"
                @click="switchCategory('features')">
              <dt class="index5">
                <a href="javascript:void(0)">模型工具</a>
              </dt>
            </dl>

            <!-- 数据源目录 -->
            <dl class="data-aggregation-nav"
                :class="{active: activeCategory === 'sources'}"
                @click="switchCategory('sources')">
              <dt class="index6">
                <a href="javascript:void(0)">数据源目录</a>
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
                    <input type="text" id="system" v-model="searchParams.system" placeholder="如 Fe-C, Al-Si-Mg">
                  </div>

                  <div class="form-group">
                    <label for="elements"><i class="fas fa-atom"></i> 元素组成</label>
                    <input type="text" id="elements" v-model="searchParams.elements" placeholder="如 Fe, C, Si">
                  </div>

                  <div class="form-group">
                    <label for="property"><i class="fas fa-chart-line"></i> 物性类型</label>
                    <select id="property" v-model="searchParams.property">
                      <option value="">选择物性类型</option>
                      <option value="CP_STD">热容 Cp</option>
                      <option value="S_STD">熵 S</option>
                      <option value="H_INCREMENT_298">焓增量 H-H298</option>
                      <option value="HF_STD">标准生成焓</option>
                      <option value="G_STD">Gibbs自由能</option>
                    </select>
                  </div>
                </div>

                <div class="form-row">
                  <div class="form-group">
                    <label for="phase"><i class="fas fa-cube"></i> 相态</label>
                    <select id="phase" v-model="searchParams.phase">
                      <option value="">全部相态</option>
                      <option value="solid">固相</option>
                      <option value="liquid">液相</option>
                      <option value="gas">气相</option>
                    </select>
                  </div>

                  <div class="form-group">
                    <label for="temperature"><i class="fas fa-thermometer-half"></i> 温度范围 (K)</label>
                    <div class="range-input">
                      <input type="number" v-model="searchParams.tempMin" placeholder="最低温">
                      <span>至</span>
                      <input type="number" v-model="searchParams.tempMax" placeholder="最高温">
                    </div>
                  </div>

                  <div class="form-group">
                    <label for="source"><i class="fas fa-book"></i> 数据来源</label>
                    <select id="source" v-model="searchParams.source">
                      <option value="">全部来源</option>
                      <option value="nist">NIST-JANAF</option>
                      <option value="calphad">CALPHAD</option>
                      <option value="experiment">实验测定</option>
                      <option value="dft">第一性原理</option>
                      <option value="materials_project">Materials Project</option>
                    </select>
                  </div>
                </div>

                <div class="form-row">
                  <div class="form-group">
                    <label for="dataType"><i class="fas fa-tag"></i> 数据类型</label>
                    <select id="dataType" v-model="searchParams.dataType">
                      <option value="">全部类型</option>
                      <option value="experimental">实验数据</option>
                      <option value="calculated">计算数据</option>
                      <option value="compiled">汇编数据</option>
                    </select>
                  </div>

                  <div class="form-group">
                    <label for="quality"><i class="fas fa-star"></i> 质量等级</label>
                    <select id="quality" v-model="searchParams.quality">
                      <option value="">全部等级</option>
                      <option value="A">A 级 — 高置信度</option>
                      <option value="B">B 级 — 中等置信度</option>
                      <option value="C">C 级 — 参考值</option>
                    </select>
                  </div>

                  <div class="form-group">
                    <label for="version"><i class="fas fa-code-branch"></i> 数据版本</label>
                    <input type="text" id="version" v-model="searchParams.version" placeholder="如 2026-01">
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
                    <th>成分</th>
                    <th>相态</th>
                    <th>物性类型</th>
                    <th>温度 (K)</th>
                    <th>数值</th>
                    <th>单位</th>
                    <th>不确定度</th>
                    <th>数据类型</th>
                    <th>来源</th>
                    <th>版本</th>
                    <th>操作</th>
                  </tr>
                  </thead>
                  <tbody>
                  <tr v-for="(item, index) in paginatedResults" :key="index">
                    <td>{{ item.system }}</td>
                    <td>{{ item.composition || '-' }}</td>
                    <td>{{ item.phase || '-' }}</td>
                    <td>{{ item.property }}</td>
                    <td>{{ item.temperature }}</td>
                    <td class="value-cell">{{ item.value }}</td>
                    <td>{{ item.unit }}</td>
                    <td>{{ item.uncertainty || '-' }}</td>
                    <td><span class="tag" :class="item.dataType">{{ item.dataTypeLabel || item.dataType || '汇编' }}</span></td>
                    <td>{{ item.source }}</td>
                    <td>{{ item.version || 'v1.0' }}</td>
                    <td class="action-cell">
                      <button class="btn-detail btn-sm" @click="viewDetail(item)" title="查看详情">
                        <i class="fas fa-info-circle"></i> 详情
                      </button>
                      <button class="btn-calc btn-sm" @click="callModel(item)" title="使用该数据计算">
                        <i class="fas fa-calculator"></i> 调用
                      </button>
                      <button class="btn-source btn-sm" @click="viewSource(item)" title="查看来源">
                        <i class="fas fa-external-link-alt"></i>
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

            <!-- 参数查询 -->
            <div class="search-section mt30">
              <div class="section-header">
                <h3><i class="fas fa-search"></i> 参数查询</h3>
                <p>查询扩散系数、指前因子、激活能等动力学参数</p>
              </div>

              <div class="search-form">
                <div class="form-row">
                  <div class="form-group">
                    <label><i class="fas fa-cubes"></i> 材料体系</label>
                    <input type="text" v-model="searchKinetics.material" placeholder="如 Fe-C, Ni基合金">
                  </div>
                  <div class="form-group">
                    <label><i class="fas fa-atom"></i> 扩散元素</label>
                    <input type="text" v-model="searchKinetics.element" placeholder="如 C, Cr, Ni">
                  </div>
                  <div class="form-group">
                    <label><i class="fas fa-microchip"></i> 基体相</label>
                    <select v-model="searchKinetics.matrix">
                      <option value="">全部</option>
                      <option value="austenite">奥氏体</option>
                      <option value="ferrite">铁素体</option>
                      <option value="liquid">液相</option>
                    </select>
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label><i class="fas fa-tag"></i> 参数类型</label>
                    <select v-model="searchKinetics.paramType">
                      <option value="">全部</option>
                      <option value="diffusion">扩散系数 D</option>
                      <option value="preexponential">指前因子 D₀</option>
                      <option value="activation">激活能 Q</option>
                      <option value="rate">反应速率常数 k</option>
                      <option value="jmak">JMAK参数</option>
                      <option value="grain">晶粒长大参数</option>
                      <option value="oxidation">氧化动力学参数</option>
                    </select>
                  </div>
                  <div class="form-group">
                    <label><i class="fas fa-thermometer-half"></i> 温度范围 (K)</label>
                    <div class="range-input">
                      <input type="number" v-model="searchKinetics.tempMin" placeholder="最低">
                      <span>至</span>
                      <input type="number" v-model="searchKinetics.tempMax" placeholder="最高">
                    </div>
                  </div>
                  <div class="form-group">
                    <label><i class="fas fa-book"></i> 数据来源</label>
                    <select v-model="searchKinetics.source">
                      <option value="">全部</option>
                      <option value="experiment">实验测定</option>
                      <option value="calphad">CALPHAD</option>
                      <option value="dft">第一性原理</option>
                      <option value="compiled">汇编数据</option>
                    </select>
                  </div>
                </div>
                <div class="form-actions">
                  <button class="btn-search" @click="searchKineticsData">
                    <i class="fas fa-search"></i> 查询参数
                  </button>
                  <button class="btn-reset" @click="resetKineticsSearch">
                    <i class="fas fa-redo"></i> 重置
                  </button>
                </div>
              </div>
            </div>

            <!-- 查询结果 -->
            <div class="data-results mt30" v-if="showKineticsResults">
              <div class="results-header">
                <h3><i class="fas fa-table"></i> 查询结果</h3>
                <div class="results-info">
                  <span>共找到 {{ kineticsResults.length }} 条记录</span>
                </div>
              </div>
              <div class="results-table">
                <table>
                  <thead>
                  <tr>
                    <th>材料体系</th>
                    <th>扩散元素</th>
                    <th>基体相</th>
                    <th>参数类型</th>
                    <th>数值</th>
                    <th>温度范围 (K)</th>
                    <th>方法</th>
                    <th>来源</th>
                    <th>质量等级</th>
                    <th>操作</th>
                  </tr>
                  </thead>
                  <tbody>
                  <tr v-for="(item, i) in paginatedKinetics" :key="i">
                    <td>{{ item.material }}</td>
                    <td>{{ item.element }}</td>
                    <td>{{ item.matrix }}</td>
                    <td>{{ item.paramType }}</td>
                    <td class="value-cell">{{ item.value }}</td>
                    <td>{{ item.tempRange }}</td>
                    <td>{{ item.method }}</td>
                    <td>{{ item.source }}</td>
                    <td><span class="tag" :class="item.quality">{{ item.qualityLabel }}</span></td>
                    <td>
                      <button class="btn-calc btn-sm" @click="callKineticsModel(item)">
                        <i class="fas fa-play"></i> 调用模型
                      </button>
                    </td>
                  </tr>
                  </tbody>
                </table>
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

            <!-- 相图计算 -->
            <div class="phase-calculator mt30">
              <div class="section-header">
                <h3><i class="fas fa-cogs"></i> 相图计算</h3>
                <p>选择计算条件，在线计算相平衡</p>
              </div>

              <div class="phase-layout">
                <!-- 左侧：计算条件 -->
                <div class="phase-left">
                  <div class="phase-params">
                    <div class="form-row">
                      <label>元素体系</label>
                      <select v-model="phaseParams.system">
                        <option value="fe-c">Fe-C</option>
                        <option value="fe-cr">Fe-Cr</option>
                        <option value="al-si">Al-Si</option>
                        <option value="cu-zn">Cu-Zn</option>
                        <option value="ti-al">Ti-Al</option>
                      </select>
                    </div>
                    <div class="form-row">
                      <label>成分 (wt.%)</label>
                      <input type="text" v-model="phaseParams.composition" placeholder="如 0.8">
                    </div>
                    <div class="form-row">
                      <label>温度 (K)</label>
                      <input type="number" v-model="phaseParams.temperature" placeholder="如 1450">
                    </div>
                    <div class="form-row">
                      <label>压力 (Pa)</label>
                      <input type="number" v-model="phaseParams.pressure" value="101325">
                    </div>
                    <div class="form-row">
                      <label>计算类型</label>
                      <select v-model="phaseParams.calcType">
                        <option value="equilibrium">平衡计算</option>
                        <option value="scheil">Scheil凝固</option>
                      </select>
                    </div>
                    <div class="form-row">
                      <label>数据库版本</label>
                      <select v-model="phaseParams.dbVersion">
                        <option value="tcfe7">TCFE7</option>
                        <option value="tcfe8">TCFE8</option>
                        <option value="pbins">PBINS</option>
                      </select>
                    </div>
                    <button class="btn-search" @click="calcPhaseDiagram">
                      <i class="fas fa-calculator"></i> 计算相图
                    </button>
                  </div>

                  <div class="available-models">
                    <h4><i class="fas fa-cogs"></i> 可调用模型</h4>
                    <div class="model-chip" @click="invokeModelById('B019')">B019 杠杆规则</div>
                    <div class="model-chip" @click="invokeModelById('B020')">B020 相界插值</div>
                    <div class="model-chip" @click="invokeModelById('B023')">B023 CALPHAD</div>
                  </div>
                </div>

                <!-- 中部：相图 -->
                <div class="phase-center">
                  <div class="phase-diagram-container">
                    <div class="mock-phase-diagram-large">
                      <div class="phase-layer liquid" style="height: 35%">
                        <span class="phase-label">液相区 (L)</span>
                      </div>
                      <div class="phase-layer mixed" style="height: 15%">
                        <span class="phase-label">L + γ</span>
                      </div>
                      <div class="phase-layer solid" style="height: 30%">
                        <span class="phase-label">γ 奥氏体</span>
                      </div>
                      <div class="phase-layer solid2" style="height: 20%">
                        <span class="phase-label">α + 渗碳体</span>
                      </div>
                      <!-- 温度刻度 -->
                      <div class="phase-scale-y">
                        <span>1800K</span>
                        <span>1400K</span>
                        <span>1000K</span>
                      </div>
                      <div class="phase-scale-x">
                        <span>Fe</span>
                        <span>0.5%</span>
                        <span>C</span>
                      </div>
                      <!-- 选中的点 -->
                      <div class="phase-dot" style="left: 40%; bottom: 55%"></div>
                    </div>
                  </div>
                </div>

                <!-- 右侧：选中点详情 -->
                <div class="phase-right">
                  <div class="phase-detail">
                    <h4>选中点详情</h4>
                    <div class="detail-row">
                      <span class="detail-label">体系</span>
                      <span class="detail-value">{{ phaseParams.system || 'Fe-C' }}</span>
                    </div>
                    <div class="detail-row">
                      <span class="detail-label">温度</span>
                      <span class="detail-value">{{ phaseParams.temperature || 1450 }} K</span>
                    </div>
                    <div class="detail-row">
                      <span class="detail-label">成分</span>
                      <span class="detail-value">{{ phaseParams.composition || '0.8' }} wt.% C</span>
                    </div>
                    <div class="detail-row">
                      <span class="detail-label">平衡相</span>
                      <span class="detail-value phase-tag">γ + L</span>
                    </div>
                    <div class="detail-row">
                      <span class="detail-label">液相分数</span>
                      <span class="detail-value">0.32</span>
                    </div>
                    <div class="detail-row">
                      <span class="detail-label">固相分数</span>
                      <span class="detail-value">0.68</span>
                    </div>
                    <div class="detail-divider"></div>
                    <div class="detail-row">
                      <span class="detail-label">调用模型</span>
                      <span class="detail-value"><code>B023</code></span>
                    </div>
                    <div class="detail-row">
                      <span class="detail-label">数据库</span>
                      <span class="detail-value">TCFE7 v1.0</span>
                    </div>
                    <button class="btn-calc" @click="invokeModelById('B023')" style="margin-top: 12px; width: 100%;">
                      <i class="fas fa-play"></i> 调用CALPHAD计算
                    </button>
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

            <!-- 数据查询 -->
            <div class="search-section mt30">
              <div class="section-header">
                <h3><i class="fas fa-search"></i> 数据查询</h3>
                <p>查询冶金反应热力学数据</p>
              </div>
              <div class="search-form">
                <div class="form-row">
                  <div class="form-group">
                    <label><i class="fas fa-arrow-right"></i> 反应物</label>
                    <input type="text" v-model="searchReaction.reactants" placeholder="如 FeO, C">
                  </div>
                  <div class="form-group">
                    <label><i class="fas fa-arrow-left"></i> 生成物</label>
                    <input type="text" v-model="searchReaction.products" placeholder="如 Fe, CO">
                  </div>
                  <div class="form-group">
                    <label><i class="fas fa-balance-scale"></i> 反应式</label>
                    <input type="text" v-model="searchReaction.reaction" placeholder="如 FeO + C → Fe + CO">
                  </div>
                </div>
                <div class="form-row">
                  <div class="form-group">
                    <label><i class="fas fa-tag"></i> 反应类别</label>
                    <select v-model="searchReaction.category">
                      <option value="">全部</option>
                      <option value="oxidation">氧化反应</option>
                      <option value="reduction">还原反应</option>
                      <option value="decomposition">分解反应</option>
                      <option value="exchange">置换反应</option>
                    </select>
                  </div>
                  <div class="form-group">
                    <label><i class="fas fa-thermometer-half"></i> 温度范围 (K)</label>
                    <div class="range-input">
                      <input type="number" v-model="searchReaction.tempMin" placeholder="最低">
                      <span>至</span>
                      <input type="number" v-model="searchReaction.tempMax" placeholder="最高">
                    </div>
                  </div>
                  <div class="form-group">
                    <label><i class="fas fa-book"></i> 数据来源</label>
                    <select v-model="searchReaction.source">
                      <option value="">全部</option>
                      <option value="nist">NIST-JANAF</option>
                      <option value="calphad">CALPHAD</option>
                      <option value="experiment">实验测定</option>
                    </select>
                  </div>
                </div>
                <div class="form-actions">
                  <button class="btn-search" @click="searchReactionData">
                    <i class="fas fa-search"></i> 查询反应
                  </button>
                </div>
              </div>
            </div>

            <!-- 查询结果 -->
            <div class="data-results mt30" v-if="showReactionResults">
              <div class="results-header">
                <h3><i class="fas fa-table"></i> 查询结果</h3>
                <span>共找到 {{ reactionResults.length }} 条反应</span>
              </div>
              <div class="results-table">
                <table>
                  <thead>
                  <tr>
                    <th>反应式</th>
                    <th>名称</th>
                    <th>ΔH (kJ/mol)</th>
                    <th>ΔS (J/mol·K)</th>
                    <th>ΔG (kJ/mol)</th>
                    <th>温度 (K)</th>
                    <th>数据来源</th>
                    <th>操作</th>
                  </tr>
                  </thead>
                  <tbody>
                  <tr v-for="(r, i) in reactionResults" :key="i">
                    <td><code>{{ r.reaction }}</code></td>
                    <td>{{ r.name }}</td>
                    <td class="value-cell">{{ r.deltaH }}</td>
                    <td>{{ r.deltaS }}</td>
                    <td class="value-cell">{{ r.deltaG }}</td>
                    <td>{{ r.temperature }}</td>
                    <td>NIST-JANAF</td>
                    <td class="action-cell">
                      <button class="btn-calc btn-sm" @click="invokeModelById('B008', r.reaction)">ΔG</button>
                      <button class="btn-calc btn-sm" @click="invokeModelById('B006', r.reaction)">ΔH</button>
                      <button class="btn-calc btn-sm" @click="invokeModelById('B009', r.reaction)">K</button>
                    </td>
                  </tr>
                  </tbody>
                </table>
              </div>
            </div>

            <!-- 在线计算 -->
            <div class="reaction-online mt30">
              <div class="section-header">
                <h3><i class="fas fa-calculator"></i> 在线计算</h3>
                <p>选中反应后调用小模型进行计算，结果带数据来源和边界校验</p>
              </div>
              <div class="online-grid">
                <div class="online-card" @click="invokeModelById('B006')">
                  <div class="online-icon"><i class="fas fa-fire"></i></div>
                  <h4>B006 反应焓计算</h4>
                  <p>ΔH = ΣΔHf°(产物) − ΣΔHf°(反应物)</p>
                  <span class="tag calculated">公式计算</span>
                </div>
                <div class="online-card" @click="invokeModelById('B007')">
                  <div class="online-icon"><i class="fas fa-random"></i></div>
                  <h4>B007 反应熵计算</h4>
                  <p>ΔS = ΣS°(产物) − ΣS°(反应物)</p>
                  <span class="tag calculated">公式计算</span>
                </div>
                <div class="online-card" @click="invokeModelById('B008')">
                  <div class="online-icon"><i class="fas fa-balance-scale"></i></div>
                  <h4>B008 Gibbs自由能计算</h4>
                  <p>ΔG = ΔH − T·ΔS + 反应方向判定</p>
                  <span class="tag compiled" style="background:#ffebee;color:#c62828;">P0 已实现</span>
                </div>
                <div class="online-card" @click="invokeModelById('B009')">
                  <div class="online-icon"><i class="fas fa-chart-line"></i></div>
                  <h4>B009 平衡常数计算</h4>
                  <p>K = exp(−ΔG°/RT)</p>
                  <span class="tag compiled" style="background:#ffebee;color:#c62828;">P0 已实现</span>
                </div>
                <div class="online-card" @click="invokeModelById('B011')">
                  <div class="online-icon"><i class="fas fa-chart-area"></i></div>
                  <h4>B011 Ellingham线计算</h4>
                  <p>ΔG°-T 图与氧势换算</p>
                  <span class="tag planned" style="background:#f3e5f5;color:#7b1fa2;">规划中</span>
                </div>
              </div>
            </div>
          </div>

          <!-- ==================== 模型工具中心 ==================== -->
          <div class="module-content" v-if="activeCategory === 'features'">
            <div class="module-header">
              <h2><i class="fas fa-cogs"></i> 模型工具中心</h2>
              <p class="module-desc">注册小模型统一调用，支持数据查询→选择模型→输入参数→执行计算→保存日志的完整链路</p>
            </div>

            <!-- 筛选栏 -->
            <div class="search-form mt20">
              <div class="form-row">
                <div class="form-group">
                  <label for="modelKeyword"><i class="fas fa-search"></i> 关键词</label>
                  <input type="text" id="modelKeyword" v-model="modelFilter.keyword" placeholder="搜索模型名称或ID">
                </div>
                <div class="form-group">
                  <label for="modelScenario"><i class="fas fa-tag"></i> 业务场景</label>
                  <select id="modelScenario" v-model="modelFilter.scenario">
                    <option value="">全部场景</option>
                    <option value="通用数据与校验">通用数据与校验</option>
                    <option value="热力学与相平衡">热力学与相平衡</option>
                    <option value="动力学与传递">动力学与传递</option>
                    <option value="转炉炼钢">转炉炼钢</option>
                    <option value="高炉炼铁">高炉炼铁</option>
                    <option value="连铸">连铸</option>
                  </select>
                </div>
                <div class="form-group">
                  <label for="modelPriority"><i class="fas fa-flag"></i> 优先级</label>
                  <select id="modelPriority" v-model="modelFilter.priority">
                    <option value="">全部</option>
                    <option value="P0">P0 — 优先实施</option>
                    <option value="P1">P1 — 重要</option>
                    <option value="P2">P2 — 一般</option>
                  </select>
                </div>
              </div>
            </div>

            <!-- 模型卡片网格 -->
            <div class="model-cards-grid mt20">
              <div class="model-card" v-for="model in filteredModels" :key="model.id">
                <div class="model-card-header">
                  <span class="model-badge" :class="'priority-' + (model.priority||'P2').toLowerCase()">{{ model.id }}</span>
                  <span class="model-priority">{{ model.priority }}</span>
                </div>
                <div class="model-card-body">
                  <h4>{{ model.name }}</h4>
                  <p class="model-desc">{{ model.scenario }}</p>
                  <span class="model-type-tag">{{ model.type }}</span>
                </div>
                <div class="model-card-footer">
                  <button class="btn-detail btn-sm" @click="openModelDetail(model)">
                    <i class="fas fa-info-circle"></i> 详情
                  </button>
                  <button class="btn-calc btn-sm" @click="invokeModel(model)">
                    <i class="fas fa-play"></i> 调用
                  </button>
                </div>
              </div>
            </div>

            <!-- 可调用工具一览 -->
            <div class="section-header mt30">
              <h3><i class="fas fa-list"></i> 可调用工具一览</h3>
              <p>已注册的 120 个小模型，按场景分类</p>
            </div>

            <div class="model-table mt10">
              <table>
                <thead>
                <tr>
                  <th>模型ID</th>
                  <th>名称</th>
                  <th>场景</th>
                  <th>类型</th>
                  <th>优先级</th>
                  <th>状态</th>
                  <th>操作</th>
                </tr>
                </thead>
                <tbody>
                <tr v-for="m in registeredModels" :key="m.model_id">
                  <td><code>{{ m.model_id }}</code></td>
                  <td>{{ m.name }}</td>
                  <td>{{ m.scenario }}</td>
                  <td>{{ m.model_type }}</td>
                  <td><span class="badge-prio" :class="'p' + (m.priority||'p2').toLowerCase()">{{ m.priority }}</span></td>
                  <td><span class="status-tag" :class="m.status || 'dev'">{{ statusLabel(m.status) }}</span></td>
                  <td>
                    <button class="btn-calc btn-sm" @click="invokeModelById(m.model_id)">
                      <i class="fas fa-play"></i> 调用
                    </button>
                  </td>
                </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- ==================== 数据源目录 ==================== -->
          <div class="module-content" v-if="activeCategory === 'sources'">
            <div class="module-header">
              <h2><i class="fas fa-book-open"></i> 数据源目录</h2>
              <p class="module-desc">44个外部数据源统一管理 — 公开数据、仅元数据/链接、需授权/内部数据，共三个接入等级</p>
            </div>

            <!-- 数据源统计卡片 -->
            <div class="echarts-data-num">
              <div class="data-item">
                <dl>
                  <dt>数据源总数</dt>
                  <dd>44</dd>
                  <dd class="trend up">持续增加</dd>
                </dl>
                <div class="card-icon">
                  <i class="fas fa-database fa-2x"></i>
                </div>
              </div>
              <div class="data-item">
                <dl>
                  <dt>公开数据</dt>
                  <dd>28</dd>
                  <dd class="trend up">直接接入</dd>
                </dl>
                <div class="card-icon">
                  <i class="fas fa-globe fa-2x"></i>
                </div>
              </div>
              <div class="data-item">
                <dl>
                  <dt>需授权/内部</dt>
                  <dd>16</dd>
                  <dd class="trend down">按需接入</dd>
                </dl>
                <div class="card-icon">
                  <i class="fas fa-lock fa-2x"></i>
                </div>
              </div>
            </div>

            <!-- 数据源表格 -->
            <div class="model-table mt30">
              <div class="section-header">
                <h3><i class="fas fa-list"></i> 数据源清单</h3>
                <p>按类别浏览外部数据源，点击查看详情</p>
              </div>
              <table>
                <thead>
                <tr>
                  <th>资料ID</th>
                  <th>一级类别</th>
                  <th>资料源</th>
                  <th>机构</th>
                  <th>访问方式</th>
                  <th>开放性</th>
                  <th>优先级</th>
                  <th>操作</th>
                </tr>
                </thead>
                <tbody>
                <tr v-for="ds in dataSources" :key="ds.id" class="clickable-row" @click="openSourceDetail(ds)">
                  <td><code>{{ ds.id }}</code></td>
                  <td>{{ ds.category }}</td>
                  <td><strong>{{ ds.name }}</strong></td>
                  <td>{{ ds.provider }}</td>
                  <td>{{ ds.access }}</td>
                  <td><span class="status-tag" :class="ds.openClass">{{ ds.openLabel }}</span></td>
                  <td><span class="badge-prio" :class="'p' + (ds.priority||'p0').toLowerCase()">{{ ds.priority }}</span></td>
                  <td>
                    <button class="btn-detail btn-sm" @click.stop="openSourceDetail(ds)" title="查看详情">
                      <i class="fas fa-info-circle"></i>
                    </button>
                    <button v-if="ds.url" class="btn-source btn-sm" @click.stop="openExternalUrl(ds.url)" title="打开外部链接">
                      <i class="fas fa-external-link-alt"></i>
                    </button>
                  </td>
                </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- 数据源详情弹窗 -->
          <div v-if="showSourceModal && sourceDetail" class="source-modal-overlay" @click="closeSourceModal">
            <div class="source-modal" @click.stop>
              <div class="source-modal-header">
                <div>
                  <h3><i class="fas fa-database"></i> {{ sourceDetail.name }}</h3>
                  <p class="source-id">数据源 ID: {{ sourceDetail.id }}</p>
                </div>
                <button class="btn-close" @click="closeSourceModal"><i class="fas fa-times"></i></button>
              </div>
              <div class="source-modal-body">
                <div class="source-info-grid">
                  <div class="info-item">
                    <label>类别</label>
                    <span>{{ sourceDetail.category }}</span>
                  </div>
                  <div class="info-item">
                    <label>机构</label>
                    <span>{{ sourceDetail.provider }}</span>
                  </div>
                  <div class="info-item">
                    <label>访问方式</label>
                    <span>{{ sourceDetail.access }}</span>
                  </div>
                  <div class="info-item">
                    <label>开放性</label>
                    <span class="status-tag" :class="sourceDetail.openClass">{{ sourceDetail.openLabel }}</span>
                  </div>
                  <div class="info-item">
                    <label>优先级</label>
                    <span class="badge-prio" :class="'p' + (sourceDetail.priority||'p0').toLowerCase()">{{ sourceDetail.priority }}</span>
                  </div>
                  <div class="info-item">
                    <label>入库策略</label>
                    <span>{{ sourceDetail.ingestion || '按需接入' }}</span>
                  </div>
                </div>
                <div v-if="sourceDetail.url" class="source-url-row">
                  <a :href="sourceDetail.url" target="_blank" class="btn-calc">
                    <i class="fas fa-external-link-alt"></i> 访问原始数据源
                  </a>
                </div>
                <div class="source-related-models">
                  <h4><i class="fas fa-cogs"></i> 关联模型</h4>
                  <div class="related-models-list">
                    <span v-for="m in relatedModels(sourceDetail.id)" :key="m" class="model-chip" @click="invokeModelById(m)">
                      {{ m }}
                    </span>
                    <span v-if="relatedModels(sourceDetail.id).length === 0" class="no-models">暂无关联模型</span>
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
        elements: '',
        property: '',
        phase: '',
        tempMin: '',
        tempMax: '',
        source: '',
        dataType: '',
        quality: '',
        version: ''
      },
      showResults: false,
      results: [],
      currentPage: 1,
      pageSize: 10,
      // 模型工具筛选
      modelFilter: {
        keyword: '',
        scenario: '',
        priority: ''
      },
      // 从后端 API 获取的模型列表
      registeredModels: [],
      // 动力学搜索参数
      searchKinetics: {
        material: '', element: '', matrix: '', paramType: '',
        tempMin: '', tempMax: '', source: ''
      },
      showKineticsResults: false,
      kineticsResults: [],
      kineticsPage: 1,
      // 相图参数
      phaseParams: {
        system: 'fe-c', composition: '0.8', temperature: 1450,
        pressure: 101325, calcType: 'equilibrium', dbVersion: 'tcfe7'
      },
      // 反应搜索参数
      searchReaction: {
        reactants: '', products: '', reaction: '',
        category: '', tempMin: '', tempMax: '', source: ''
      },
      showReactionResults: false,
      reactionResults: [],
      sourceDetail: null,        // 当前查看的数据源详情
    showSourceModal: false,
      // 数据源目录数据
      dataSources: [
        { id: 'DS001', category: '热化学/物性', name: 'NIST Chemistry WebBook', provider: 'NIST', access: '网页/批量下载', openLabel: '公开', openClass: 'open', priority: 'P0', url: 'https://webbook.nist.gov/chemistry/' },
        { id: 'DS002', category: '热化学/物性', name: 'NIST-JANAF Thermochemical Tables', provider: 'NIST', access: '网页/表格', openLabel: '公开', openClass: 'open', priority: 'P0', url: 'https://janaf.nist.gov/' },
        { id: 'DS003', category: '材料计算', name: 'Materials Project', provider: 'LBNL', access: 'REST API', openLabel: 'API访问', openClass: 'open', priority: 'P0', url: 'https://materialsproject.org/' },
        { id: 'DS004', category: '材料计算', name: 'OQMD', provider: 'Northwestern Univ.', access: 'REST API/下载', openLabel: '开放', openClass: 'open', priority: 'P1', url: 'https://oqmd.org/' },
        { id: 'DS005', category: '材料计算', name: 'AFLOW', provider: 'AFLOW Consortium', access: 'API/下载', openLabel: '开放', openClass: 'open', priority: 'P1', url: 'https://aflow.org/' },
        { id: 'DS006', category: '材料计算', name: 'NOMAD', provider: 'FAIR-DI', access: 'API/下载', openLabel: '开放', openClass: 'open', priority: 'P1', url: 'https://nomad-lab.eu/' },
        { id: 'DS007', category: '材料计算', name: 'ASE/AFLOW/XML prototype', provider: 'NREL/AFLOW', access: '下载', openLabel: '开放', openClass: 'open', priority: 'P1' },
        { id: 'DS010', category: '热力学数据', name: 'FACT/FTlite/FSsteel', provider: 'CRCT-ThermFact', access: '商业许可', openLabel: '需授权', openClass: 'restricted', priority: 'P0' },
        { id: 'DS011', category: '热力学数据', name: 'TCS/TTNl/TTFe/TTMg', provider: 'Thermo-Calc', access: '商业许可', openLabel: '需授权', openClass: 'restricted', priority: 'P1' },
        { id: 'DS020', category: '冶金工艺', name: 'GB/T 标准库', provider: '中国标准化院', access: '内部扫描', openLabel: '内部', openClass: 'internal', priority: 'P0' },
        { id: 'DS031', category: '标准/规范', name: 'ISO/TC 17/SC', provider: 'ISO', access: '商业采购', openLabel: '需授权', openClass: 'restricted', priority: 'P1' },
        { id: 'DS040', category: '基础数据工具', name: 'IUPAC 原子量', provider: 'IUPAC', access: 'API', openLabel: '公开', openClass: 'open', priority: 'P0', url: 'https://iupac.org/' },
        { id: 'DS042', category: '基础数据工具', name: 'CODATA 物理常数', provider: 'NIST', access: '网页', openLabel: '公开', openClass: 'open', priority: 'P0', url: 'https://physics.nist.gov/cuu/Constants/' },
      ],
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
    },
    paginatedKinetics() {
      const s = (this.kineticsPage - 1) * 10;
      return this.kineticsResults.slice(s, s + 10);
    },
    paginatedReactions() {
      const s = (this.reactionPage - 1) * 10;
      return this.reactionResults.slice(s, s + 10);
    },
    // 筛选的模型卡片（本地模拟）
    filteredModels() {
      let list = this.modelCardData;
      if (this.modelFilter.keyword) {
        const kw = this.modelFilter.keyword.toLowerCase();
        list = list.filter(m => m.id.toLowerCase().includes(kw) || m.name.includes(kw));
      }
      if (this.modelFilter.scenario) {
        list = list.filter(m => m.scenario === this.modelFilter.scenario);
      }
      if (this.modelFilter.priority) {
        list = list.filter(m => m.priority === this.modelFilter.priority);
      }
      return list;
    },
    // 本地模拟模型卡片数据（实际从后端 API 获取）
    modelCardData() {
      return [
        { id: 'A001', name: '单位换算', scenario: '通用数据与校验', type: '确定性公式', priority: 'P0' },
        { id: 'A002', name: '化学式解析', scenario: '通用数据与校验', type: '确定性公式', priority: 'P0' },
        { id: 'A003', name: '摩尔质量计算', scenario: '通用数据与校验', type: '确定性公式', priority: 'P0' },
        { id: 'A004', name: '成分归一化', scenario: '通用数据与校验', type: '规则校验', priority: 'P0' },
        { id: 'A005', name: '质量守恒校验', scenario: '通用数据与校验', type: '规则校验', priority: 'P0' },
        { id: 'B001', name: 'Shomate热容计算', scenario: '热力学与相平衡', type: '多项式', priority: 'P0' },
        { id: 'B002', name: 'NASA多项式热物性', scenario: '热力学与相平衡', type: '多项式', priority: 'P0' },
        { id: 'B003', name: '显热与焓积分', scenario: '热力学与相平衡', type: '数值积分', priority: 'P0' },
        { id: 'B004', name: '熵积分', scenario: '热力学与相平衡', type: '数值积分', priority: 'P0' },
        { id: 'B005', name: '物种Gibbs自由能', scenario: '热力学与相平衡', type: '确定性公式', priority: 'P0' },
        { id: 'B006', name: '反应焓计算', scenario: '热力学与相平衡', type: '确定性公式', priority: 'P0' },
        { id: 'B007', name: '反应熵计算', scenario: '热力学与相平衡', type: '确定性公式', priority: 'P0' },
        { id: 'B008', name: 'Gibbs自由能计算', scenario: '热力学与相平衡', type: '确定性公式', priority: 'P0' },
        { id: 'B009', name: '平衡常数计算', scenario: '热力学与相平衡', type: '确定性公式', priority: 'P0' },
        { id: 'B019', name: '杠杆规则计算', scenario: '热力学与相平衡', type: '确定性公式', priority: 'P2' },
        { id: 'C001', name: 'Arrhenius速率常数', scenario: '动力学与传递', type: '确定性公式', priority: 'P0' },
        { id: 'C002', name: '扩散系数计算', scenario: '动力学与传递', type: '确定性公式', priority: 'P0' },
      ];
    }
  },
  methods: {
    switchCategory(category) {
      this.activeCategory = category;
    },

    // ── 热力学搜索（调后端 API）──
    searchData() {
      this.showResults = true;
      this.currentPage = 1;

      const params = new URLSearchParams();
      if (this.searchParams.system) params.append('species', this.searchParams.system);
      if (this.searchParams.property) params.append('property_type', this.searchParams.property);
      if (this.searchParams.quality) params.append('quality', this.searchParams.quality);
      if (this.searchParams.tempMin) params.append('temp_min', this.searchParams.tempMin);
      if (this.searchParams.tempMax) params.append('temp_max', this.searchParams.tempMax);

      fetch(`/api/v1/data/thermodynamics?page_size=2000&${params.toString()}`)
        .then(r => r.json())
        .then(data => {
          if (data.data && data.data.length > 0) {
            this.results = data.data.map(r => ({
              system: r.species ? r.species.replace(/\([^)]*\)/g,'') : '-',
              composition: r.species || '-',
              phase: r.species ? (r.species.includes('(l)')?'液相':r.species.includes('(g)')?'气相':'固相') : '-',
              property: ({
                'Cp': '热容 Cp',
                'S': '熵 S',
                'H-H298': '焓增量 H-H298',
                'H_INCREMENT_298': '焓增量 H-H298',
                '生成焓_ΔHf°': '标准生成焓',
                'CP_STD': '热容 Cp',
                'S_STD': '熵 S',
                'G_STD': 'Gibbs自由能',
                'HF_STD': '标准生成焓',
              })[r.property_type] || r.property_type,
              temperature: r.temperature || '-',
              value: r.value,
              unit: r.unit || '',
              uncertainty: r.uncertainty || '-',
              dataTypeLabel: ({
                'calculated': '计算值',
                'experimental': '实验值',
                'compiled': '汇编值',
              })[r.data_type] || r.data_type || '汇编',
              dataType: r.data_type || 'compiled',
              source: r.source_ref ? r.source_ref.replace(' NIST-JANAF Shomate','') : (r.dataset_id || '-'),
              version: 'v1.0',
            }));
          } else {
            // 降级：API 没数据时显示空结果
            this.results = [];
          }
        })
        .catch(err => {
          console.warn('热力学 API 不可用', err);
          this.results = [];
        });
    },

    // ── 从 API 获取数据源目录 ──
    fetchSources() {
      fetch('/api/v1/data/sources')
        .then(r => r.json())
        .then(data => {
          if (data.sources && data.sources.length > 0) {
            this.dataSources = data.sources.map(s => ({
              id: s.dataset_id,
              category: s.category,
              name: s.name,
              provider: s.provider || '-',
              access: s.ingestion_mode || '网页',
              openLabel: s.security_level === '公开' ? '公开' : s.security_level === '内部' ? '内部' : '需授权',
              openClass: s.security_level === '公开' ? 'open' : s.security_level === '内部' ? 'internal' : 'restricted',
              priority: 'P0',
              url: s.access_url || '',
              ingestion: s.ingestion_mode,
            }));
          }
        })
        .catch(err => console.warn('数据源 API 不可用，使用本地数据', err));
    },

    // ── 重置热力学搜索 ──
    resetSearch() {
      this.searchParams = {
        system: '', elements: '', property: '', phase: '',
        tempMin: '', tempMax: '', source: '', dataType: '', quality: '', version: ''
      };
      this.showResults = false;
      this.results = [];
      this.currentPage = 1;
    },

    exportData() {
      alert('数据导出功能开发中...');
    },

    viewDetail(item) {
      alert(`查看详情：\n合金体系：${item.system}\n成分：${item.composition}\n相态：${item.phase}\n物性类型：${item.property}\n温度：${item.temperature}K\n数值：${item.value} ${item.unit}\n不确定度：${item.uncertainty}\n数据类型：${item.dataTypeLabel}\n来源：${item.source}\n版本：${item.version}`);
    },

    callModel(item) {
      // 根据数据类型跳转到对应的模型调用页面
      const modelMap = {
        '生成焓': 'B006',
        'Gibbs自由能': 'B008',
        '熵': 'B007',
        '热容 (Cp)': 'B003',
        '扩散系数': 'C002',
        '相图数据': 'B023',
      };
      const modelId = modelMap[item.property] || 'B008';
      this.$router.push(`/scene?model=${modelId}&data=${encodeURIComponent(JSON.stringify(item))}`);
    },

    viewSource(item) {
      const sourceUrls = {
        'NIST-JANAF': 'https://janaf.nist.gov/',
        'CALPHAD': 'https://www.calphad.org/',
        'Materials Project': 'https://materialsproject.org/',
        '实验数据': '',
        '实验测定': '',
        '第一性原理': '',
        '热力学数据库': '',
      };
      const url = sourceUrls[item.source];
      if (url) {
        window.open(url, '_blank');
      } else {
        alert(`来源：${item.source}\n版本：${item.version}\n该来源暂未配置外部链接`);
      }
    },

    openCalculator(type) {
      alert(`打开${type}计算器...`);
    },

    // ── 模型工具方法 ──

    statusLabel(status) {
      const labels = { planned: '规划中', dev: '开发中', validated: '已验证', deployed: '已部署' };
      return labels[status] || status || '开发中';
    },

    openModelDetail(model) {
      alert(`模型详情：${model.id} ${model.name}\n场景：${model.scenario}\n类型：${model.type}\n优先级：${model.priority}\n说明：基于统一Tool Schema注册，支持前端自动生成调用表单。`);
    },

    invokeModel(model) {
      this.$router.push(`/scene?model=${model.id}`);
    },

    invokeModelById(modelId, reaction) {
      let query = `?model=${modelId}`;
      if (reaction) query += `&reaction=${encodeURIComponent(reaction)}`;
      this.$router.push(`/scene${query}`);
    },

    // 从后端 API 获取模型列表
    async fetchModels() {
      try {
        const resp = await fetch('/api/v1/models');
        if (resp.ok) {
          const data = await resp.json();
          this.registeredModels = data.models || [];
        }
      } catch (e) {
        console.warn('模型微服务不可用，使用本地模拟数据', e.message);
        // 降级为本地模拟
        this.registeredModels = this.modelCardData.map(m => ({
          model_id: m.id, name: m.name, scenario: m.scenario,
          model_type: m.type, priority: m.priority, status: 'dev',
        }));
      }
    },

    openSourceDetail(ds) {
      this.sourceDetail = { ...ds, ingestion: ds.ingestion || (ds.access === 'REST API' ? 'API增量同步' : ds.access === '网页' ? '结构化抽取' : '按需接入') };
      this.showSourceModal = true;
    },
    closeSourceModal() { this.showSourceModal = false; this.sourceDetail = null; },
    openExternalUrl(url) { window.open(url, '_blank'); },
    relatedModels(dsId) {
      const map = {
        'DS001': ['B001','B002'], 'DS002': ['B006','B007','B008','B009'],
        'DS003': ['B022','B023'], 'DS031': ['B023'], 'DS040': ['A002','A003'],
        'DS042': ['A001','C001'],
      };
      return map[dsId] || [];
    },

    // ── 动力学方法 ──
    searchKineticsData() {
      this.showKineticsResults = true;
      this.kineticsPage = 1;
      this.kineticsResults = [
        { material: 'Fe-C', element: 'C', matrix: '奥氏体', paramType: '扩散系数 D', value: '2.3e-11 m²/s', tempRange: '1273-1473', method: '扩散偶实验', source: '实验测定', quality: 'experimental', qualityLabel: '实验' },
        { material: 'Fe-C', element: 'C', matrix: '铁素体', paramType: '扩散系数 D', value: '6.2e-12 m²/s', tempRange: '1073-1273', method: '扩散偶实验', source: '实验测定', quality: 'experimental', qualityLabel: '实验' },
        { material: 'Ni-Cr', element: 'Cr', matrix: '奥氏体', paramType: '指前因子 D₀', value: '1.8e-4 m²/s', tempRange: '1173-1573', method: 'CALPHAD评估', source: 'CALPHAD', quality: 'calculated', qualityLabel: '计算' },
        { material: 'Fe-C', element: 'C', matrix: '奥氏体', paramType: '激活能 Q', value: '148 kJ/mol', tempRange: '298-2000', method: 'Arrhenius拟合', source: '汇编数据', quality: 'compiled', qualityLabel: '汇编' },
        { material: 'Al-Cu', element: 'Cu', matrix: '液相', paramType: '扩散系数 D', value: '3.2e-9 m²/s', tempRange: '973-1073', method: '毛细管法', source: '实验测定', quality: 'experimental', qualityLabel: '实验' },
        { material: 'Fe-C', element: 'C', matrix: '奥氏体', paramType: '反应速率常数 k', value: '0.045 mol/(m²·s)', tempRange: '1373', method: '热重分析', source: '实验室', quality: 'experimental', qualityLabel: '实验' },
      ];
    },
    resetKineticsSearch() {
      this.searchKinetics = { material: '', element: '', matrix: '', paramType: '', tempMin: '', tempMax: '', source: '' };
      this.showKineticsResults = false;
      this.kineticsResults = [];
    },
    callKineticsModel(item) {
      const modelMap = { '扩散系数 D': 'C002', '反应速率常数 k': 'C001', '指前因子 D₀': 'C002', '激活能 Q': 'C001' };
      const mid = modelMap[item.paramType] || 'C001';
      this.$router.push(`/scene?model=${mid}`);
    },

    // ── 相图方法 ──
    calcPhaseDiagram() {
      alert(`计算相图：${this.phaseParams.system} @ ${this.phaseParams.temperature}K\n成分：${this.phaseParams.composition} wt.%\n计算类型：${this.phaseParams.calcType}\n此功能需后端 B023 CALPHAD 模型支持`);
    },

    // ── 反应方法 ──
    searchReactionData() {
      this.showReactionResults = true;
      this.reactionPage = 1;
      this.reactionResults = [
        { reaction: 'C + O₂ → CO₂', name: '碳完全燃烧', deltaH: -393.5, deltaS: 2.9, deltaG: -394.4, temperature: 298, source: 'NIST-JANAF' },
        { reaction: 'FeO + C → Fe + CO', name: '氧化亚铁直接还原', deltaH: 158.0, deltaS: 150.0, deltaG: 113.3, temperature: 298, source: 'NIST-JANAF' },
        { reaction: 'CaCO₃ → CaO + CO₂', name: '石灰石煅烧', deltaH: 178.3, deltaS: 160.6, deltaG: 130.4, temperature: 298, source: 'NIST-JANAF' },
        { reaction: '2Fe + O₂ → 2FeO', name: '铁氧化', deltaH: -544.0, deltaS: -159.4, deltaG: -496.5, temperature: 298, source: 'NIST-JANAF' },
        { reaction: 'SiO₂ + 2C → Si + 2CO', name: '工业硅冶炼', deltaH: 689.6, deltaS: 359.3, deltaG: 582.5, temperature: 298, source: 'NIST-JANAF' },
      ];
    },
  },
  mounted() {
    this.fetchSources();
    this.fetchModels();
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

/* ── 新增工具按钮样式 ── */
.btn-sm {
  padding: 4px 10px;
  font-size: 12px;
  border-radius: 4px;
}
.btn-calc {
  background: linear-gradient(135deg, #00B4FF, #0095E8);
  color: white;
  border: none;
  padding: 4px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.3s;
}
.btn-calc:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(0, 180, 255, 0.3);
}
.btn-source {
  background: transparent;
  color: #666;
  border: 1px solid #ddd;
  padding: 4px 10px;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.3s;
}
.btn-source:hover {
  background: #f5f5f5;
  border-color: #0046DB;
  color: #0046DB;
}
.action-cell {
  display: flex;
  gap: 4px;
  align-items: center;
  white-space: nowrap;
}

/* ── 数据类型标签 ── */
.tag {
  display: inline-block;
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 11px;
  font-weight: 500;
}
.tag.experimental { background: #e3f2fd; color: #1565c0; }
.tag.calculated { background: #fce4ec; color: #c62828; }
.tag.compiled { background: #e8f5e9; color: #2e7d32; }

/* ── 模型卡片网格 ── */
.model-cards-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 16px;
}
.model-card {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-radius: 12px;
  padding: 16px;
  transition: all 0.3s;
  display: flex;
  flex-direction: column;
}
.model-card:hover {
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
  transform: translateY(-2px);
  border-color: #0046DB;
}
.model-card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.model-badge {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 700;
  font-family: monospace;
}
.model-badge.priority-p0 { background: #ffebee; color: #c62828; }
.model-badge.priority-p1 { background: #fff8e1; color: #f57f17; }
.model-badge.priority-p2 { background: #e8f5e9; color: #2e7d32; }
.model-priority {
  font-size: 11px;
  color: #999;
}
.model-card-body h4 {
  margin: 4px 0;
  font-size: 15px;
  color: #333;
}
.model-card-body .model-desc {
  margin: 2px 0;
  font-size: 12px;
  color: #999;
}
.model-type-tag {
  display: inline-block;
  padding: 1px 6px;
  background: #f0f0f0;
  border-radius: 4px;
  font-size: 11px;
  color: #666;
}
.model-card-footer {
  display: flex;
  gap: 8px;
  margin-top: auto;
  padding-top: 12px;
}

/* ── 状态标签 ── */
.status-tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 10px;
  font-size: 12px;
  font-weight: 500;
}
.status-tag.open { background: #e8f5e9; color: #2e7d32; }
.status-tag.restricted { background: #fff8e1; color: #f57f17; }
.status-tag.internal { background: #ffebee; color: #c62828; }
.status-tag.planned { background: #f3e5f5; color: #7b1fa2; }
.status-tag.dev { background: #fff8e1; color: #f57f17; }
.status-tag.validated { background: #e3f2fd; color: #1565c0; }
.status-tag.deployed { background: #e8f5e9; color: #2e7d32; }

.badge-prio { display: inline-block; padding: 2px 8px; border-radius: 8px; font-size: 11px; font-weight: 600; }
.badge-prio.pp0 { background: #ffebee; color: #c62828; }
.badge-prio.pp1 { background: #fff8e1; color: #f57f17; }
.badge-prio.pp2 { background: #e8f5e9; color: #2e7d32; }

/* ── 模型/数据源表格 ── */
.model-table {
  background: #fff;
  border-radius: 12px;
  padding: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
}
.model-table table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}
.model-table th {
  text-align: left;
  padding: 10px 12px;
  font-weight: 600;
  color: #666;
  border-bottom: 2px solid #eef0f4;
  font-size: 12px;
  white-space: nowrap;
}
.model-table td {
  padding: 8px 12px;
  border-bottom: 1px solid #f0f0f0;
}
.model-table td code {
  background: #f5f5f5;
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 12px;
}
.model-table tr:hover td {
  background: #fafbfc;
}
.clickable-row { cursor: pointer; transition: background 0.2s; }
.clickable-row:hover td { background: #e8f0fe !important; }

/* ── 数据源详情弹窗 ── */
.source-modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000; display: flex; align-items: center; justify-content: center; }
.source-modal { background: #fff; border-radius: 16px; width: 560px; max-width: 90vw; max-height: 80vh; overflow-y: auto; box-shadow: 0 20px 60px rgba(0,0,0,0.2); }
.source-modal-header { display: flex; justify-content: space-between; align-items: flex-start; padding: 24px 28px 16px; border-bottom: 1px solid #eef0f4; }
.source-modal-header h3 { margin: 0; font-size: 18px; color: #333; display: flex; align-items: center; gap: 8px; }
.source-modal-header h3 i { color: #0046DB; }
.source-id { font-size: 12px; color: #999; margin: 4px 0 0; }
.source-modal-body { padding: 20px 28px 28px; }
.source-info-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.info-item { display: flex; flex-direction: column; gap: 4px; }
.info-item label { font-size: 11px; color: #999; text-transform: uppercase; letter-spacing: 0.5px; }
.info-item span { font-size: 14px; color: #333; }
.source-url-row { margin-top: 20px; text-align: center; }
.source-url-row .btn-calc { display: inline-flex; align-items: center; gap: 6px; padding: 10px 24px; font-size: 14px; text-decoration: none; border-radius: 8px; }
.source-related-models { margin-top: 20px; padding-top: 16px; border-top: 1px solid #eef0f4; }
.source-related-models h4 { font-size: 13px; color: #333; margin: 0 0 10px; display: flex; align-items: center; gap: 4px; }
.related-models-list { display: flex; flex-wrap: wrap; gap: 6px; }
.no-models { font-size: 12px; color: #ccc; }

.mt20 { margin-top: 20px; }

/* ── 相图三栏布局 ── */
.phase-layout { display: grid; grid-template-columns: 260px 1fr 260px; gap: 20px; margin-top: 20px; }
.phase-left { background: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.05); }
.phase-params { display: flex; flex-direction: column; gap: 12px; }
.phase-params .form-row { display: flex; flex-direction: column; gap: 4px; }
.phase-params .form-row label { font-size: 12px; color: #666; font-weight: 500; }
.phase-params .form-row input,
.phase-params .form-row select { padding: 6px 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 13px; }
.phase-params .btn-search { margin-top: 8px; width: 100%; }
.available-models { margin-top: 20px; padding-top: 16px; border-top: 1px solid #eef0f4; }
.available-models h4 { font-size: 13px; color: #333; margin: 0 0 8px; display: flex; align-items: center; gap: 4px; }
.model-chip { display: inline-block; padding: 4px 10px; background: #f0f4ff; border: 1px solid rgba(0,70,219,0.15); border-radius: 14px; font-size: 12px; cursor: pointer; margin: 2px; color: #0046DB; transition: all 0.2s; }
.model-chip:hover { background: #0046DB; color: #fff; }

.phase-center { min-height: 400px; }
.phase-diagram-container { background: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.05); height: 100%; }
.mock-phase-diagram-large { position: relative; height: 360px; background: linear-gradient(to bottom, #fff5f5 0%, #fff 40%, #e8f5e9 100%); border: 1px solid #ddd; border-radius: 8px; overflow: hidden; display: flex; flex-direction: column; justify-content: flex-end; }
.phase-layer { position: relative; display: flex; align-items: center; justify-content: center; border-top: 1px dashed rgba(255,255,255,0.5); transition: all 0.3s; }
.phase-layer.liquid { background: linear-gradient(135deg, rgba(0,70,219,0.15), rgba(0,180,255,0.1)); }
.phase-layer.mixed { background: repeating-linear-gradient(45deg, rgba(0,70,219,0.08), rgba(0,70,219,0.08) 8px, rgba(0,180,255,0.08) 8px, rgba(0,180,255,0.08) 16px); }
.phase-layer.solid { background: linear-gradient(135deg, rgba(64,192,87,0.12), rgba(76,205,196,0.08)); }
.phase-layer.solid2 { background: linear-gradient(135deg, rgba(150,206,180,0.15), rgba(200,230,201,0.1)); }
.phase-label { font-size: 13px; font-weight: 600; color: #333; text-shadow: 0 1px 2px rgba(255,255,255,0.8); }
.phase-scale-y { position: absolute; left: 4px; top: 0; height: 100%; display: flex; flex-direction: column; justify-content: space-between; padding: 4px 0; font-size: 10px; color: #999; }
.phase-scale-x { position: absolute; bottom: -20px; left: 0; width: 100%; display: flex; justify-content: space-between; padding: 0 10px; font-size: 10px; color: #999; }
.phase-dot { position: absolute; width: 12px; height: 12px; background: #e53935; border: 2px solid #fff; border-radius: 50%; box-shadow: 0 2px 6px rgba(0,0,0,0.3); transform: translate(-50%, 50%); cursor: pointer; z-index: 2; }

.phase-right { background: #fff; border-radius: 12px; padding: 20px; box-shadow: 0 2px 12px rgba(0,0,0,0.05); }
.phase-detail h4 { font-size: 14px; color: #333; margin: 0 0 12px; padding-bottom: 8px; border-bottom: 2px solid #0046DB; }
.detail-row { display: flex; justify-content: space-between; align-items: center; padding: 6px 0; font-size: 13px; border-bottom: 1px solid #f5f5f5; }
.detail-label { color: #999; }
.detail-value { color: #333; font-weight: 500; }
.detail-value.phase-tag { color: #0046DB; font-weight: 600; }
.detail-value code { background: #f5f5f5; padding: 2px 6px; border-radius: 3px; font-size: 12px; }
.detail-divider { height: 1px; background: #eef0f4; margin: 8px 0; }

/* ── 在线计算卡片 ── */
.online-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(200px, 1fr)); gap: 14px; }
.online-card { background: #fff; border: 1px solid #e8e8e8; border-radius: 12px; padding: 16px; cursor: pointer; transition: all 0.3s; }
.online-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.08); border-color: #0046DB; transform: translateY(-2px); }
.online-icon { width: 40px; height: 40px; background: #f0f4ff; border-radius: 10px; display: flex; align-items: center; justify-content: center; margin-bottom: 10px; }
.online-icon i { font-size: 18px; color: #0046DB; }
.online-card h4 { font-size: 14px; color: #333; margin: 0 0 4px; }
.online-card p { font-size: 12px; color: #999; margin: 0 0 8px; line-height: 1.4; }

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