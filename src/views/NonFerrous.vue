<template>
  <Header></Header>
  <div class="nonferrous">
    <!-- 面包屑导航 -->
    <div class="mb-nav">
      <div class="container">
        <p>
          当前位置： <router-link to="/">首页</router-link> >
          <span>有色冶金</span>
        </p>
      </div>
    </div>

    <!-- ==================== Hero 区域 ==================== -->
    <section class="hero-section">
      <div class="hero-overlay"></div>
      <div class="container hero-content">
        <h1 class="hero-title">有色冶金</h1>
        <p class="hero-subtitle">
          覆盖铝、铜、锌、镁、稀土等有色金属从矿物加工到金属提纯的全流程工艺数据库与智能分析平台
        </p>
        <div class="hero-stats">
          <div class="hero-stat-item">
            <span class="hero-stat-number">50,000+</span>
            <span class="hero-stat-label">工艺数据</span>
          </div>
          <div class="hero-stat-divider"></div>
          <div class="hero-stat-item">
            <span class="hero-stat-number">30+</span>
            <span class="hero-stat-label">金属种类</span>
          </div>
          <div class="hero-stat-divider"></div>
          <div class="hero-stat-item">
            <span class="hero-stat-number">200+</span>
            <span class="hero-stat-label">工艺路线</span>
          </div>
        </div>
      </div>
    </section>

    <!-- ==================== 概览区域 ==================== -->
    <section class="overview-section">
      <div class="container">
        <div class="section-header-center">
          <h2><i class="fas fa-industry"></i> 行业概览</h2>
          <p>有色金属是现代工业的重要基础材料，广泛应用于航空航天、电子信息、新能源等领域</p>
        </div>

        <!-- 行业统计数据 -->
        <div class="stats-row">
          <div class="stat-card">
            <div class="stat-icon">
              <i class="fas fa-chart-line"></i>
            </div>
            <div class="stat-content">
              <div class="stat-number">7,000+ 万吨</div>
              <div class="stat-label">年产量（中国）</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">
              <i class="fas fa-globe-asia"></i>
            </div>
            <div class="stat-content">
              <div class="stat-number">50%+</div>
              <div class="stat-label">全球产量占比</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">
              <i class="fas fa-building"></i>
            </div>
            <div class="stat-content">
              <div class="stat-number">10,000+</div>
              <div class="stat-label">相关企业</div>
            </div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">
              <i class="fas fa-flask"></i>
            </div>
            <div class="stat-content">
              <div class="stat-number">200+</div>
              <div class="stat-label">研究机构</div>
            </div>
          </div>
        </div>

        <!-- 概述文字 -->
        <div class="overview-text">
          <p>
            有色冶金（Non-ferrous Metallurgy）是指从矿石、精矿或二次资源中提取和加工有色金属的科学技术与工程领域。
            与黑色金属（钢铁）不同，有色金属通常具有更高的耐腐蚀性、更好的导电导热性能以及更轻的重量，
            在国民经济和国防建设中占据不可替代的地位。
          </p>
          <p>
            中国是世界上最大的有色金属生产国和消费国，拥有完整的产业链条，
            在铝、铜、锌、镁、稀土等金属的冶炼技术方面已达到国际先进水平。
            本平台汇集了丰富的有色冶金工艺数据，涵盖火法冶金、湿法冶金、电冶金三大技术路线，
            为科研人员和工程技术人员提供全方位的技术支撑。
          </p>
        </div>
      </div>
    </section>

    <!-- ==================== 主要金属分类 ==================== -->
    <section class="metals-section">
      <div class="container">
        <div class="section-header-center">
          <h2><i class="fas fa-cubes"></i> 主要金属类别</h2>
          <p>涵盖四大类关键有色金属，提供工艺参数、热力学数据与应用案例</p>
        </div>

        <div class="metals-grid">
          <!-- 铝 -->
          <div class="metal-card">
            <div class="metal-card-header">
              <div class="metal-icon">
                <i class="fas fa-plane"></i>
              </div>
              <h3>铝 (Aluminium)</h3>
            </div>
            <p class="metal-desc">
              铝是地壳中含量最丰富的金属元素，具有质轻、导电导热性好、耐腐蚀等优良特性，
              广泛应用于航空航天、建筑交通、电子电气等领域。中国是全球最大的铝生产国，年产量占世界一半以上。
            </p>
            <div class="metal-methods">
              <h4><i class="fas fa-cog"></i> 主要提取方法</h4>
              <ul>
                <li><i class="fas fa-check-circle"></i> 拜耳法 - 从铝土矿生产氧化铝</li>
                <li><i class="fas fa-check-circle"></i> 霍尔-埃鲁电解法 - 熔盐电解生产金属铝</li>
                <li><i class="fas fa-check-circle"></i> 再生铝回收 - 废铝重熔与精炼</li>
              </ul>
            </div>
            <div class="metal-apps">
              <h4><i class="fas fa-thumbs-up"></i> 关键应用</h4>
              <div class="app-tags">
                <span class="app-tag">航空航天</span>
                <span class="app-tag">汽车轻量化</span>
                <span class="app-tag">建筑幕墙</span>
                <span class="app-tag">电力电缆</span>
                <span class="app-tag">食品包装</span>
              </div>
            </div>
          </div>

          <!-- 铜 -->
          <div class="metal-card">
            <div class="metal-card-header">
              <div class="metal-icon">
                <i class="fas fa-bolt"></i>
              </div>
              <h3>铜 (Copper)</h3>
            </div>
            <p class="metal-desc">
              铜是人类最早使用的金属之一，以其优良的导电性、导热性和延展性著称，
              是电子电气工业的基础材料。铜及铜合金在电力传输、通信电子、建筑管道、机械制造等领域有广泛应用。
            </p>
            <div class="metal-methods">
              <h4><i class="fas fa-cog"></i> 主要提取方法</h4>
              <ul>
                <li><i class="fas fa-check-circle"></i> 火法炼铜 - 闪速熔炼与转炉吹炼</li>
                <li><i class="fas fa-check-circle"></i> 湿法炼铜 - 浸出-萃取-电积工艺</li>
                <li><i class="fas fa-check-circle"></i> 电解精炼 - 高纯阴极铜生产</li>
              </ul>
            </div>
            <div class="metal-apps">
              <h4><i class="fas fa-thumbs-up"></i> 关键应用</h4>
              <div class="app-tags">
                <span class="app-tag">电力传输</span>
                <span class="app-tag">电子器件</span>
                <span class="app-tag">通信线缆</span>
                <span class="app-tag">建筑管道</span>
                <span class="app-tag">新能源汽车</span>
              </div>
            </div>
          </div>

          <!-- 锌/镁 -->
          <div class="metal-card">
            <div class="metal-card-header">
              <div class="metal-icon">
                <i class="fas fa-shield-alt"></i>
              </div>
              <h3>锌与镁 (Zinc &amp; Magnesium)</h3>
            </div>
            <p class="metal-desc">
              锌主要用于钢材镀锌防腐，镁是最轻的结构金属材料。锌在电池、合金制造中作用显著；
              镁合金因其比重小、比强度高，在汽车轻量化、3C电子产品、航空航天等领域需求持续增长。
            </p>
            <div class="metal-methods">
              <h4><i class="fas fa-cog"></i> 主要提取方法</h4>
              <ul>
                <li><i class="fas fa-check-circle"></i> 锌：焙烧-浸出-电解沉积工艺</li>
                <li><i class="fas fa-check-circle"></i> 镁：皮江法硅热还原工艺</li>
                <li><i class="fas fa-check-circle"></i> 镁：熔盐电解法生产</li>
              </ul>
            </div>
            <div class="metal-apps">
              <h4><i class="fas fa-thumbs-up"></i> 关键应用</h4>
              <div class="app-tags">
                <span class="app-tag">钢材镀锌</span>
                <span class="app-tag">锌基电池</span>
                <span class="app-tag">镁合金压铸</span>
                <span class="app-tag">3C电子外壳</span>
                <span class="app-tag">生物医用材料</span>
              </div>
            </div>
          </div>

          <!-- 稀土 -->
          <div class="metal-card">
            <div class="metal-card-header">
              <div class="metal-icon">
                <i class="fas fa-atom"></i>
              </div>
              <h3>稀土金属 (Rare Earths)</h3>
            </div>
            <p class="metal-desc">
              稀土元素包括镧系元素及钪、钇等17种元素，被誉为"工业维生素"。
              稀土在永磁材料、催化材料、发光材料、储氢材料等高新技术领域不可或缺，
              中国拥有全球最完整的稀土产业链和最大的生产规模。
            </p>
            <div class="metal-methods">
              <h4><i class="fas fa-cog"></i> 主要提取方法</h4>
              <ul>
                <li><i class="fas fa-check-circle"></i> 溶剂萃取分离 - 稀土元素分组与提纯</li>
                <li><i class="fas fa-check-circle"></i> 离子交换法 - 高纯稀土制备</li>
                <li><i class="fas fa-check-circle"></i> 熔盐电解 - 稀土金属及其合金生产</li>
              </ul>
            </div>
            <div class="metal-apps">
              <h4><i class="fas fa-thumbs-up"></i> 关键应用</h4>
              <div class="app-tags">
                <span class="app-tag">永磁材料</span>
                <span class="app-tag">催化裂化</span>
                <span class="app-tag">LED荧光粉</span>
                <span class="app-tag">储氢合金</span>
                <span class="app-tag">激光晶体</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ==================== 应用领域 ==================== -->
    <section class="applications-section">
      <div class="container">
        <div class="section-header-center">
          <h2><i class="fas fa-rocket"></i> 应用领域</h2>
          <p>有色金属在国民经济各领域发挥着关键作用，是现代化建设的重要物质基础</p>
        </div>

        <div class="apps-grid">
          <div class="app-card">
            <div class="app-card-icon">
              <i class="fas fa-satellite"></i>
            </div>
            <h3>航空航天</h3>
            <p>铝合金机身结构、钛合金发动机部件、镁合金航天器零件、稀土永磁电机</p>
          </div>
          <div class="app-card">
            <div class="app-card-icon">
              <i class="fas fa-car"></i>
            </div>
            <h3>交通运输</h3>
            <p>汽车轻量化铝合金车身、铜合金线束、镁合金轮毂、锌基合金模具</p>
          </div>
          <div class="app-card">
            <div class="app-card-icon">
              <i class="fas fa-microchip"></i>
            </div>
            <h3>电子信息</h3>
            <p>高纯铜引线框架、铝基电路板、稀土永磁扬声器、锌锰电池材料</p>
          </div>
          <div class="app-card">
            <div class="app-card-icon">
              <i class="fas fa-sun"></i>
            </div>
            <h3>新能源</h3>
            <p>光伏用多晶硅、锂电池铝箔、风电用稀土永磁、核能用锆合金</p>
          </div>
          <div class="app-card">
            <div class="app-card-icon">
              <i class="fas fa-hard-hat"></i>
            </div>
            <h3>建筑与基础设施</h3>
            <p>铝合金门窗幕墙、铜质水管、镀锌钢材、铝模板支撑系统</p>
          </div>
          <div class="app-card">
            <div class="app-card-icon">
              <i class="fas fa-heartbeat"></i>
            </div>
            <h3>生物医疗</h3>
            <p>钛合金人工关节、镁合金骨钉、银系抗菌材料、金基药物载体</p>
          </div>
        </div>
      </div>
    </section>

    <!-- ==================== 技术路线 ==================== -->
    <section class="tech-section">
      <div class="container">
        <div class="section-header-center">
          <h2><i class="fas fa-project-diagram"></i> 主要技术路线</h2>
          <p>有色冶金涵盖三大技术路线，适应不同矿物特性和产品要求</p>
        </div>

        <div class="tech-cards">
          <div class="tech-card-item">
            <div class="tech-card-number">01</div>
            <h3>火法冶金</h3>
            <p>利用高温从矿石中提取金属，包括焙烧、熔炼、吹炼、精炼等工序。适用于硫化矿和氧化矿的处理，是铜、镍、铅等金属的主要生产方法。</p>
            <ul class="tech-features">
              <li><i class="fas fa-fire"></i> 高温反应过程</li>
              <li><i class="fas fa-tachometer-alt"></i> 生产效率高</li>
              <li><i class="fas fa-industry"></i> 规模化生产</li>
            </ul>
          </div>
          <div class="tech-card-item">
            <div class="tech-card-number">02</div>
            <h3>湿法冶金</h3>
            <p>在溶液中进行金属提取与分离，包括浸出、萃取、离子交换、电积等工序。适用于低品位矿和复杂共生矿的处理，环境友好程度更高。</p>
            <ul class="tech-features">
              <li><i class="fas fa-tint"></i> 溶液过程</li>
              <li><i class="fas fa-leaf"></i> 环境友好</li>
              <li><i class="fas fa-layer-group"></i> 适用低品位矿</li>
            </ul>
          </div>
          <div class="tech-card-item">
            <div class="tech-card-number">03</div>
            <h3>电冶金</h3>
            <p>以电能作为能源进行金属提取和精炼，包括熔盐电解、水溶液电解等方法。是铝、镁等活泼金属的唯一工业生产方法，也用于铜的电解精炼。</p>
            <ul class="tech-features">
              <li><i class="fas fa-bolt"></i> 电化学过程</li>
              <li><i class="fas fa-battery-full"></i> 产品纯度高</li>
              <li><i class="fas fa-microscope"></i> 精密控制</li>
            </ul>
          </div>
        </div>
      </div>
    </section>

    <!-- ==================== CTA 区域 ==================== -->
    <section class="cta-section">
      <div class="container">
        <div class="cta-content">
          <h2>探索有色冶金数据库</h2>
          <p>访问丰富的工艺参数、热力学数据与应用案例，助力科研与工程创新</p>
          <router-link to="/search" class="cta-button">
            <i class="fas fa-search"></i> 立即查询
          </router-link>
        </div>
      </div>
    </section>
  </div>
  <Footer></Footer>
</template>

<script>
import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";

export default {
  name: "NonFerrous",
  components: {
    Header,
    Footer,
  },
};
</script>

<style scoped>
/* ==================== 基础样式 ==================== */
.nonferrous {
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

/* ==================== 面包屑导航 ==================== */
.mb-nav {
  background: #fff;
  border-bottom: 1px solid #eee;
  padding: 12px 0;
}

.mb-nav p {
  font-size: 14px;
  color: #666;
  margin: 0;
}

.mb-nav a {
  color: #0046DB;
  text-decoration: none;
  transition: color 0.3s;
}

.mb-nav a:hover {
  color: #0035a8;
}

.mb-nav span {
  color: #333;
  font-weight: 500;
}

/* ==================== Hero 区域 ==================== */
.hero-section {
  position: relative;
  background: linear-gradient(135deg, #001a4d 0%, #003380 40%, #0046DB 100%);
  min-height: 360px;
  display: flex;
  align-items: center;
  overflow: hidden;
}

.hero-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background:
    radial-gradient(ellipse at 20% 50%, rgba(0, 180, 255, 0.15) 0%, transparent 50%),
    radial-gradient(ellipse at 80% 20%, rgba(255, 255, 255, 0.05) 0%, transparent 50%);
  pointer-events: none;
}

.hero-content {
  position: relative;
  z-index: 1;
  text-align: center;
  padding: 60px 0;
}

.hero-title {
  font-size: 42px;
  font-weight: 700;
  color: #fff;
  margin: 0 0 16px 0;
  letter-spacing: 4px;
}

.hero-subtitle {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.85);
  max-width: 720px;
  margin: 0 auto 40px;
  line-height: 1.8;
}

.hero-stats {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0;
}

.hero-stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0 40px;
}

.hero-stat-number {
  font-size: 32px;
  font-weight: 700;
  color: #fff;
  margin-bottom: 6px;
}

.hero-stat-label {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.75);
}

.hero-stat-divider {
  width: 1px;
  height: 50px;
  background: rgba(255, 255, 255, 0.25);
}

/* ==================== 通用区域标题 ==================== */
.section-header-center {
  text-align: center;
  margin-bottom: 40px;
}

.section-header-center h2 {
  font-size: 30px;
  color: #222;
  margin: 0 0 12px 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.section-header-center h2 i {
  color: #0046DB;
  font-size: 26px;
}

.section-header-center p {
  font-size: 15px;
  color: #888;
  margin: 0;
  max-width: 600px;
  margin: 0 auto;
  line-height: 1.6;
}

/* ==================== 概览区域 ==================== */
.overview-section {
  padding: 60px 0;
  background: #fff;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 20px;
  margin-bottom: 40px;
}

.stat-card {
  background: #fff;
  border-radius: 12px;
  padding: 24px;
  text-align: center;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
  transition: all 0.3s;
}

.stat-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 70, 219, 0.12);
  border-color: #0046DB;
}

.stat-icon {
  font-size: 36px;
  color: #0046DB;
  margin-bottom: 14px;
}

.stat-number {
  font-size: 26px;
  font-weight: 700;
  color: #0046DB;
  margin-bottom: 6px;
}

.stat-label {
  font-size: 14px;
  color: #888;
}

.overview-text {
  max-width: 900px;
  margin: 0 auto;
}

.overview-text p {
  font-size: 15px;
  color: #555;
  line-height: 1.9;
  margin: 0 0 16px 0;
  text-indent: 2em;
}

.overview-text p:last-child {
  margin-bottom: 0;
}

/* ==================== 金属分类卡片 ==================== */
.metals-section {
  padding: 60px 0;
  background: #f5f7fa;
}

.metals-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
}

.metal-card {
  background: #fff;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
  transition: all 0.3s;
}

.metal-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 28px rgba(0, 70, 219, 0.10);
  border-color: #0046DB;
}

.metal-card-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 2px solid #f0f0f0;
}

.metal-icon {
  width: 56px;
  height: 56px;
  background: linear-gradient(135deg, #0046DB, #0066ff);
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #fff;
  flex-shrink: 0;
}

.metal-card-header h3 {
  font-size: 22px;
  color: #222;
  margin: 0;
}

.metal-desc {
  font-size: 14px;
  color: #666;
  line-height: 1.8;
  margin: 0 0 20px 0;
}

.metal-methods {
  margin-bottom: 16px;
}

.metal-methods h4,
.metal-apps h4 {
  font-size: 15px;
  color: #333;
  margin: 0 0 10px 0;
  display: flex;
  align-items: center;
  gap: 6px;
}

.metal-methods h4 i,
.metal-apps h4 i {
  color: #0046DB;
  font-size: 14px;
}

.metal-methods ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.metal-methods ul li {
  font-size: 13px;
  color: #555;
  padding: 6px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.metal-methods ul li i {
  color: #0046DB;
  font-size: 14px;
}

.app-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.app-tag {
  display: inline-block;
  padding: 4px 12px;
  background: rgba(0, 70, 219, 0.08);
  color: #0046DB;
  font-size: 12px;
  border-radius: 20px;
  transition: all 0.3s;
}

.app-tag:hover {
  background: #0046DB;
  color: #fff;
}

/* ==================== 应用领域 ==================== */
.applications-section {
  padding: 60px 0;
  background: #fff;
}

.apps-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 20px;
}

.app-card {
  background: #fff;
  border-radius: 12px;
  padding: 28px;
  text-align: center;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
  transition: all 0.3s;
}

.app-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 24px rgba(0, 70, 219, 0.10);
  border-color: #0046DB;
}

.app-card-icon {
  width: 60px;
  height: 60px;
  background: linear-gradient(135deg, #0046DB, #0066ff);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #fff;
  margin: 0 auto 16px;
}

.app-card h3 {
  font-size: 18px;
  color: #222;
  margin: 0 0 10px 0;
}

.app-card p {
  font-size: 14px;
  color: #888;
  line-height: 1.7;
  margin: 0;
}

/* ==================== 技术路线 ==================== */
.tech-section {
  padding: 60px 0;
  background: #f5f7fa;
}

.tech-cards {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 24px;
}

.tech-card-item {
  background: #fff;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
  transition: all 0.3s;
  position: relative;
  overflow: hidden;
}

.tech-card-item:hover {
  transform: translateY(-4px);
  box-shadow: 0 8px 28px rgba(0, 70, 219, 0.10);
  border-color: #0046DB;
}

.tech-card-number {
  font-size: 48px;
  font-weight: 800;
  color: rgba(0, 70, 219, 0.06);
  position: absolute;
  top: 10px;
  right: 16px;
  line-height: 1;
  user-select: none;
}

.tech-card-item h3 {
  font-size: 20px;
  color: #222;
  margin: 0 0 14px 0;
  position: relative;
}

.tech-card-item h3::after {
  content: '';
  display: block;
  width: 40px;
  height: 3px;
  background: #0046DB;
  margin-top: 8px;
  border-radius: 2px;
}

.tech-card-item > p {
  font-size: 14px;
  color: #666;
  line-height: 1.8;
  margin: 0 0 18px 0;
}

.tech-features {
  list-style: none;
  padding: 0;
  margin: 0;
}

.tech-features li {
  font-size: 13px;
  color: #555;
  padding: 6px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.tech-features li i {
  color: #0046DB;
  font-size: 14px;
  width: 18px;
  text-align: center;
}

/* ==================== CTA 区域 ==================== */
.cta-section {
  padding: 60px 0;
  background: linear-gradient(135deg, #001a4d 0%, #0046DB 100%);
}

.cta-content {
  text-align: center;
}

.cta-content h2 {
  font-size: 30px;
  color: #fff;
  margin: 0 0 14px 0;
}

.cta-content p {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.8);
  margin: 0 0 30px 0;
}

.cta-button {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 14px 40px;
  background: #fff;
  color: #0046DB;
  font-size: 16px;
  font-weight: 600;
  border-radius: 30px;
  text-decoration: none;
  transition: all 0.3s;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
}

.cta-button:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 28px rgba(0, 0, 0, 0.25);
  background: #f0f4ff;
}

/* ==================== 响应式设计 ==================== */
@media (max-width: 1200px) {
  .container {
    max-width: 960px;
  }

  .hero-title {
    font-size: 36px;
  }

  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }

  .apps-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (max-width: 992px) {
  .metals-grid {
    grid-template-columns: 1fr;
  }

  .tech-cards {
    grid-template-columns: 1fr;
  }

  .hero-section {
    min-height: 300px;
  }

  .hero-title {
    font-size: 30px;
  }

  .hero-stats {
    flex-wrap: wrap;
    gap: 10px;
  }

  .hero-stat-item {
    padding: 0 24px;
  }

  .hero-stat-divider {
    display: none;
  }

  .hero-stat-number {
    font-size: 26px;
  }

  .nonferrous {
    padding-top: 80px;
  }
}

@media (max-width: 768px) {
  .hero-title {
    font-size: 26px;
    letter-spacing: 2px;
  }

  .hero-subtitle {
    font-size: 14px;
  }

  .hero-content {
    padding: 40px 0;
  }

  .stats-row {
    grid-template-columns: 1fr;
    gap: 14px;
  }

  .apps-grid {
    grid-template-columns: 1fr;
  }

  .section-header-center h2 {
    font-size: 24px;
  }

  .section-header-center p {
    font-size: 14px;
  }

  .overview-section,
  .metals-section,
  .applications-section,
  .tech-section {
    padding: 40px 0;
  }

  .metal-card {
    padding: 20px;
  }

  .metal-card-header h3 {
    font-size: 18px;
  }

  .app-card {
    padding: 20px;
  }

  .stat-number {
    font-size: 22px;
  }

  .cta-section {
    padding: 40px 0;
  }

  .cta-content h2 {
    font-size: 24px;
  }

  .cta-button {
    padding: 12px 32px;
    font-size: 15px;
  }
}

@media (max-width: 576px) {
  .container {
    padding: 0 12px;
  }

  .hero-title {
    font-size: 22px;
  }

  .hero-stat-item {
    padding: 0 12px;
  }

  .hero-stat-number {
    font-size: 22px;
  }

  .section-header-center {
    margin-bottom: 28px;
  }

  .section-header-center h2 {
    font-size: 20px;
  }

  .metal-card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }

  .metal-icon {
    width: 44px;
    height: 44px;
    font-size: 18px;
  }

  .app-card-icon {
    width: 50px;
    height: 50px;
    font-size: 20px;
  }

  .tech-card-number {
    font-size: 36px;
  }
}

/* 动画效果 */
@keyframes fadeInUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.hero-content,
.stat-card,
.metal-card,
.app-card,
.tech-card-item,
.cta-content {
  animation: fadeInUp 0.5s ease-out;
}
</style>
