<template>
  <Header></Header>
  <div class="basic-principles">
    <!-- 面包屑导航 -->
    <div class="mb-nav">
      <div class="container">
        <p>
          当前位置： <router-link to="/">首页</router-link> >
          <span>冶金基础原理</span>
        </p>
      </div>
    </div>

    <!-- ==================== Hero 区域 ==================== -->
    <section class="hero-section">
      <div class="hero-overlay"></div>
      <div class="container hero-content">
        <h1 class="hero-title">冶金基础原理</h1>
        <p class="hero-subtitle">Fundamental Principles of Metallurgy</p>
        <p class="hero-desc">
          系统掌握冶金过程的核心理论基础，从微观原子尺度到宏观工艺流程，全面理解金属材料的
          制备、加工与性能调控的科学原理
        </p>
        <div class="hero-stats">
          <div class="hero-stat-item">
            <span class="hero-stat-number">30+</span>
            <span class="hero-stat-label">年研究积累</span>
          </div>
          <div class="hero-stat-divider"></div>
          <div class="hero-stat-item">
            <span class="hero-stat-number">2,800+</span>
            <span class="hero-stat-label">学术论文</span>
          </div>
          <div class="hero-stat-divider"></div>
          <div class="hero-stat-item">
            <span class="hero-stat-number">150+</span>
            <span class="hero-stat-label">研究团队</span>
          </div>
          <div class="hero-stat-divider"></div>
          <div class="hero-stat-item">
            <span class="hero-stat-number">500+</span>
            <span class="hero-stat-label">应用案例</span>
          </div>
        </div>
      </div>
    </section>

    <!-- ==================== 学科概览 ==================== -->
    <section class="overview-section">
      <div class="container">
        <div class="section-header">
          <h2>学科概述</h2>
          <div class="section-line"></div>
          <p class="section-desc">冶金基础原理是材料科学与工程的核心支柱，涵盖从热力学、动力学到传输现象的完整知识体系</p>
        </div>

        <div class="overview-content">
          <div class="overview-text">
            <p>
              冶金学是研究金属及其合金的提取、加工、性能调控和应用的综合性科学。冶金基础原理构成了
              整个冶金学科的理论基石，为理解金属材料在高温条件下的物理化学行为提供了系统的理论框架。
              这些原理不仅指导着传统钢铁冶金工艺的优化与创新，也为先进金属材料的设计与开发提供了不可
              或缺的理论支撑。
            </p>
            <p>
              在现代冶金研究中，基础原理的应用已从经验性工艺参数调整提升至基于第一性原理的精确预测
              与设计。通过深入理解冶金过程中的热力学驱动力、动力学路径、相变机制以及传输行为，研究
              人员能够在原子、微观组织和宏观工艺等多个尺度上实现对材料性能的精确调控。
            </p>
            <p>
              本平台系统整合了冶金基础原理的四个核心领域——冶金热力学、冶金动力学、相变原理和传输
              现象，为冶金工程技术人员、科研工作者和高校师生提供全面的理论基础与数据支持。
            </p>
          </div>
          <div class="overview-image">
            <div class="overview-image-placeholder">
              <i class="fas fa-atom"></i>
              <span>冶金多尺度研究框架</span>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ==================== 关键统计数据 ==================== -->
    <section class="stats-section">
      <div class="container">
        <div class="stats-grid">
          <div class="stats-card" v-for="stat in statsData" :key="stat.id">
            <div class="stats-card-icon">
              <i :class="stat.icon"></i>
            </div>
            <div class="stats-card-content">
              <div class="stats-number" ref="statNumbers">{{ stat.value }}</div>
              <div class="stats-label">{{ stat.label }}</div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ==================== 核心基础理论 ==================== -->
    <section class="topics-section">
      <div class="container">
        <div class="section-header">
          <h2>核心基础理论</h2>
          <div class="section-line"></div>
          <p class="section-desc">冶金基础原理的四大核心领域，构成了完整的理论体系</p>
        </div>

        <div class="topics-grid">
          <div
            class="topic-card"
            v-for="topic in topicsData"
            :key="topic.id"
            @click="viewTopicDetail(topic)"
          >
            <div class="topic-card-inner">
              <div class="topic-icon-wrapper">
                <i :class="topic.icon"></i>
              </div>
              <h3 class="topic-title">{{ topic.title }}</h3>
              <p class="topic-desc">{{ topic.description }}</p>
              <ul class="topic-points">
                <li v-for="point in topic.points" :key="point">
                  <i class="fas fa-check-circle"></i> {{ point }}
                </li>
              </ul>
              <div class="topic-footer">
                <span class="topic-link">
                  了解更多 <i class="fas fa-arrow-right"></i>
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- ==================== 基础理论的重要性 ==================== -->
    <section class="importance-section">
      <div class="container">
        <div class="section-header">
          <h2>基础理论的重要性</h2>
          <div class="section-line"></div>
          <p class="section-desc">冶金基础原理对现代工业与科技发展的深远影响</p>
        </div>

        <div class="importance-grid">
          <div class="importance-card" v-for="item in importanceData" :key="item.id">
            <div class="importance-number">{{ item.number }}</div>
            <div class="importance-content">
              <h3>{{ item.title }}</h3>
              <p>{{ item.description }}</p>
            </div>
          </div>
        </div>

        <div class="importance-quote">
          <div class="quote-icon"><i class="fas fa-quote-left"></i></div>
          <blockquote>
            冶金基础原理不仅是对自然规律的认知，更是推动金属材料从经验走向科学的桥梁。
            在"双碳"战略背景下，基础原理的创新应用正引领着绿色冶金与智能制造的转型方向。
          </blockquote>
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
  name: "BasicPrinciples",
  components: {
    Header,
    Footer,
  },
  data() {
    return {
      statsData: [
        {
          id: 1,
          icon: "fas fa-flask",
          value: "30+",
          label: "冶金研究积累（年）",
        },
        {
          id: 2,
          icon: "fas fa-file-alt",
          value: "2,800+",
          label: "学术论文发表",
        },
        {
          id: 3,
          icon: "fas fa-users",
          value: "150+",
          label: "研究团队规模",
        },
        {
          id: 4,
          icon: "fas fa-industry",
          value: "500+",
          label: "工业应用案例",
        },
      ],
      topicsData: [
        {
          id: "thermodynamics",
          icon: "fas fa-fire",
          title: "冶金热力学",
          description:
            "研究冶金体系中能量转化与平衡规律，为判断反应方向和限度提供理论基础",
          points: [
            "Gibbs自由能与反应驱动力分析",
            "相平衡与活度预测模型",
            "多组分体系热力学计算",
            "高温冶金反应热效应评估",
          ],
        },
        {
          id: "kinetics",
          icon: "fas fa-tachometer-alt",
          title: "冶金动力学",
          description:
            "研究冶金过程中化学反应速率与传质行为，揭示过程进行的速度与路径",
          points: [
            "扩散过程与传质动力学",
            "界面反应动力学机制",
            "晶粒长大与再结晶行为",
            "微观组织演变过程模拟",
          ],
        },
        {
          id: "phase",
          icon: "fas fa-chart-pie",
          title: "相变原理",
          description:
            "研究金属材料中相的形成、转变与稳定性，指导材料组织与性能调控",
          points: [
            "凝固过程与结晶理论",
            "固态相变动力学与热力学",
            "相图分析与计算预测",
            "相变产物组织与性能关系",
          ],
        },
        {
          id: "transport",
          icon: "fas fa-water",
          title: "传输现象",
          description:
            "研究冶金过程中的热量、质量和动量传递规律，支撑工艺过程优化与设备设计",
          points: [
            "高温传热机制与热管理",
            "多相流传输行为分析",
            "传质过程与浓度场模拟",
            "冶金反应器流动特性",
          ],
        },
      ],
      importanceData: [
        {
          id: 1,
          number: "01",
          title: "指导工艺创新",
          description:
            "热力学与动力学原理为开发新型冶金工艺提供了科学的判断依据，使工程师能够预测反应方向、优化工艺参数，大幅减少试错成本，加速技术迭代。",
        },
        {
          id: 2,
          number: "02",
          title: "支撑材料设计",
          description:
            "相变原理与传输现象理论使研究人员能够在微观尺度上预测和控制材料的组织结构，进而定制化设计具有特定性能的金属材料，满足航空航天、新能源等高端领域的需求。",
        },
        {
          id: 3,
          number: "03",
          title: "推动绿色转型",
          description:
            '在"双碳"战略背景下，冶金基础原理的深入应用为低碳冶金技术路线提供了理论指导，助力氢冶金、短流程炼钢等减排工艺的研发与应用。',
        },
        {
          id: 4,
          number: "04",
          title: "赋能智能制造",
          description:
            "基础原理与大数据、人工智能的深度融合正在开创冶金智能化的新范式，实现从经验驱动到数据驱动、从离线优化到在线控制的跨越式发展。",
        },
      ],
    };
  },
  methods: {
    viewTopicDetail(topic) {
      // 导航到对应的详细页面
      const routes = {
        thermodynamics: "/thermodynamics",
        kinetics: "/thermodynamics",
        phase: "/thermodynamics",
        transport: "/fluid-dynamics",
      };
      const route = routes[topic.id] || "/";
      this.$router.push(route);
    },
  },
  mounted() {
    // 滚动动画观察者
    const observerOptions = {
      threshold: 0.15,
      rootMargin: "0px 0px -50px 0px",
    };

    const observer = new IntersectionObserver((entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("animate-in");
          observer.unobserve(entry.target);
        }
      });
    }, observerOptions);

    // 观察需要动画的元素
    const animateElements = document.querySelectorAll(
      ".topic-card, .stats-card, .importance-card, .overview-content, .importance-quote"
    );
    animateElements.forEach((el) => {
      el.classList.add("animate-ready");
      observer.observe(el);
    });
  },
};
</script>

<style scoped>
/* ==================== 基础样式 ==================== */
.basic-principles {
  background-color: #f5f7fa;
  min-height: 100vh;
  font-family: "Microsoft YaHei", "Segoe UI", Arial, sans-serif;
  padding-top: 80px;
}

.container {
  width: 100%;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 15px;
}

/* ==================== 通用部分标题 ==================== */
.section-header {
  text-align: center;
  margin-bottom: 50px;
}

.section-header h2 {
  font-size: 32px;
  color: #1a1a2e;
  margin: 0 0 16px 0;
  font-weight: 700;
  letter-spacing: 1px;
}

.section-line {
  width: 60px;
  height: 4px;
  background: linear-gradient(90deg, #0046DB, #4a7dff);
  border-radius: 2px;
  margin: 0 auto 18px;
}

.section-desc {
  font-size: 16px;
  color: #666;
  margin: 0;
  max-width: 640px;
  margin-left: auto;
  margin-right: auto;
  line-height: 1.6;
}

/* ==================== Hero 区域 ==================== */
.hero-section {
  position: relative;
  min-height: 480px;
  display: flex;
  align-items: center;
  background: linear-gradient(135deg, #0a1628 0%, #002a67 40%, #0046DB 100%);
  overflow: hidden;
}

.hero-overlay {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(ellipse at 20% 50%, rgba(0, 70, 219, 0.3) 0%, transparent 60%),
    radial-gradient(ellipse at 80% 20%, rgba(74, 125, 255, 0.2) 0%, transparent 50%),
    radial-gradient(ellipse at 50% 80%, rgba(0, 42, 103, 0.4) 0%, transparent 50%);
  pointer-events: none;
}

.hero-content {
  position: relative;
  z-index: 1;
  padding: 80px 0;
  text-align: center;
}

.hero-title {
  font-size: 48px;
  font-weight: 800;
  color: #fff;
  margin: 0 0 12px;
  letter-spacing: 3px;
  text-shadow: 0 2px 12px rgba(0, 0, 0, 0.3);
}

.hero-subtitle {
  font-size: 20px;
  color: rgba(255, 255, 255, 0.7);
  margin: 0 0 24px;
  font-weight: 300;
  letter-spacing: 4px;
  text-transform: uppercase;
}

.hero-desc {
  font-size: 17px;
  color: rgba(255, 255, 255, 0.85);
  margin: 0 auto 50px;
  max-width: 720px;
  line-height: 1.8;
}

/* Hero 统计数据 */
.hero-stats {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 0;
  flex-wrap: wrap;
}

.hero-stat-item {
  padding: 0 40px;
  text-align: center;
}

.hero-stat-number {
  display: block;
  font-size: 36px;
  font-weight: 800;
  color: #fff;
  margin-bottom: 6px;
  letter-spacing: 1px;
}

.hero-stat-label {
  font-size: 14px;
  color: rgba(255, 255, 255, 0.7);
  font-weight: 400;
}

.hero-stat-divider {
  width: 1px;
  height: 50px;
  background: rgba(255, 255, 255, 0.2);
}

/* ==================== 学科概览 ==================== */
.overview-section {
  padding: 80px 0;
  background: #fff;
}

.overview-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 50px;
  align-items: center;
}

.overview-text p {
  font-size: 15px;
  color: #444;
  line-height: 1.9;
  margin: 0 0 18px;
  text-align: justify;
}

.overview-text p:last-child {
  margin-bottom: 0;
}

.overview-image {
  display: flex;
  justify-content: center;
  align-items: center;
}

.overview-image-placeholder {
  width: 100%;
  max-width: 420px;
  aspect-ratio: 4 / 3;
  background: linear-gradient(135deg, #f0f4ff 0%, #e8eeff 100%);
  border-radius: 16px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 20px;
  border: 2px dashed #bfd4ff;
  transition: all 0.3s;
}

.overview-image-placeholder:hover {
  border-color: #0046DB;
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 70, 219, 0.12);
}

.overview-image-placeholder i {
  font-size: 72px;
  color: #0046DB;
  opacity: 0.6;
}

.overview-image-placeholder span {
  font-size: 16px;
  color: #0046DB;
  font-weight: 500;
}

/* ==================== 统计数据区域 ==================== */
.stats-section {
  padding: 60px 0;
  background: #f5f7fa;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 24px;
}

.stats-card {
  background: #fff;
  border-radius: 12px;
  padding: 30px 24px;
  display: flex;
  align-items: center;
  gap: 20px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
  transition: all 0.4s;
  cursor: default;
}

.stats-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 32px rgba(0, 70, 219, 0.12);
  border-color: #0046DB;
}

.stats-card-icon {
  width: 56px;
  height: 56px;
  min-width: 56px;
  background: linear-gradient(135deg, rgba(0, 70, 219, 0.08), rgba(0, 70, 219, 0.02));
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 26px;
  color: #0046DB;
}

.stats-card-content {
  flex: 1;
}

.stats-number {
  font-size: 28px;
  font-weight: 800;
  color: #0046DB;
  margin-bottom: 4px;
  line-height: 1.2;
}

.stats-label {
  font-size: 13px;
  color: #888;
  font-weight: 400;
}

/* ==================== 核心基础理论 ==================== */
.topics-section {
  padding: 80px 0;
  background: #fff;
}

.topics-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 28px;
}

.topic-card {
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
  transition: all 0.4s cubic-bezier(0.25, 0.46, 0.45, 0.94);
  cursor: pointer;
  overflow: hidden;
}

.topic-card:hover {
  transform: translateY(-8px);
  box-shadow: 0 20px 48px rgba(0, 70, 219, 0.15);
  border-color: #0046DB;
}

.topic-card-inner {
  padding: 36px 32px;
}

.topic-icon-wrapper {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #0046DB, #3366ff);
  border-radius: 16px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
  transition: all 0.4s;
  box-shadow: 0 6px 16px rgba(0, 70, 219, 0.25);
}

.topic-card:hover .topic-icon-wrapper {
  transform: scale(1.05) rotate(-5deg);
  box-shadow: 0 8px 24px rgba(0, 70, 219, 0.35);
}

.topic-icon-wrapper i {
  font-size: 28px;
  color: #fff;
}

.topic-title {
  font-size: 20px;
  color: #1a1a2e;
  margin: 0 0 12px;
  font-weight: 700;
  transition: color 0.3s;
}

.topic-card:hover .topic-title {
  color: #0046DB;
}

.topic-desc {
  font-size: 14px;
  color: #666;
  line-height: 1.7;
  margin: 0 0 18px;
}

.topic-points {
  list-style: none;
  padding: 0;
  margin: 0 0 20px;
}

.topic-points li {
  font-size: 13px;
  color: #555;
  padding: 5px 0;
  display: flex;
  align-items: center;
  gap: 8px;
}

.topic-points li i {
  color: #0046DB;
  font-size: 14px;
  flex-shrink: 0;
}

.topic-footer {
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.topic-link {
  font-size: 14px;
  color: #0046DB;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  transition: all 0.3s;
}

.topic-link i {
  font-size: 12px;
  transition: transform 0.3s;
}

.topic-card:hover .topic-link i {
  transform: translateX(4px);
}

/* ==================== 重要性区域 ==================== */
.importance-section {
  padding: 80px 0;
  background: #f5f7fa;
}

.importance-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24px;
  margin-bottom: 60px;
}

.importance-card {
  background: #fff;
  border-radius: 12px;
  padding: 32px 28px;
  display: flex;
  gap: 24px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  border: 1px solid #f0f0f0;
  transition: all 0.4s;
}

.importance-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 32px rgba(0, 70, 219, 0.1);
  border-color: #0046DB;
}

.importance-number {
  font-size: 40px;
  font-weight: 800;
  color: #0046DB;
  opacity: 0.15;
  line-height: 1;
  min-width: 50px;
  font-family: "Georgia", serif;
}

.importance-content h3 {
  font-size: 18px;
  color: #1a1a2e;
  margin: 0 0 10px;
  font-weight: 700;
}

.importance-content p {
  font-size: 14px;
  color: #666;
  line-height: 1.8;
  margin: 0;
}

/* 引用块 */
.importance-quote {
  background: #fff;
  border-radius: 12px;
  padding: 40px 48px;
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.05);
  border-left: 4px solid #0046DB;
  position: relative;
}

.quote-icon {
  position: absolute;
  top: 24px;
  left: 48px;
  font-size: 32px;
  color: #0046DB;
  opacity: 0.12;
}

.importance-quote blockquote {
  font-size: 17px;
  color: #444;
  line-height: 1.9;
  margin: 0;
  padding-left: 40px;
  font-style: italic;
  font-weight: 400;
}

/* ==================== 动画效果 ==================== */
.animate-ready {
  opacity: 0;
  transform: translateY(30px);
  transition: opacity 0.6s ease-out, transform 0.6s ease-out;
}

.animate-in {
  opacity: 1;
  transform: translateY(0);
}

/* 为每个卡片添加不同的延迟 */
.topic-card:nth-child(1),
.stats-card:nth-child(1),
.importance-card:nth-child(1) {
  transition-delay: 0.05s;
}

.topic-card:nth-child(2),
.stats-card:nth-child(2),
.importance-card:nth-child(2) {
  transition-delay: 0.1s;
}

.topic-card:nth-child(3),
.stats-card:nth-child(3),
.importance-card:nth-child(3) {
  transition-delay: 0.15s;
}

.topic-card:nth-child(4),
.stats-card:nth-child(4),
.importance-card:nth-child(4) {
  transition-delay: 0.2s;
}

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

/* ==================== 响应式设计 ==================== */
@media (max-width: 1200px) {
  .container {
    max-width: 960px;
  }

  .hero-title {
    font-size: 40px;
  }

  .hero-stat-item {
    padding: 0 28px;
  }

  .stats-grid {
    gap: 16px;
  }
}

@media (max-width: 992px) {
  .overview-content {
    grid-template-columns: 1fr;
    gap: 30px;
  }

  .overview-image {
    order: -1;
  }

  .overview-image-placeholder {
    max-width: 100%;
    height: 200px;
  }

  .topics-grid {
    gap: 20px;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .importance-grid {
    grid-template-columns: 1fr;
  }

  .hero-title {
    font-size: 34px;
  }

  .hero-stats {
    gap: 0;
  }

  .hero-stat-item {
    padding: 0 20px;
  }

  .hero-stat-number {
    font-size: 28px;
  }
}

@media (max-width: 768px) {
  .basic-principles {
    padding-top: 80px;
  }

  .hero-section {
    min-height: 380px;
  }

  .hero-content {
    padding: 50px 0;
  }

  .hero-title {
    font-size: 28px;
  }

  .hero-subtitle {
    font-size: 15px;
    letter-spacing: 2px;
  }

  .hero-desc {
    font-size: 14px;
    margin-bottom: 35px;
  }

  .hero-stats {
    flex-direction: column;
    gap: 16px;
  }

  .hero-stat-divider {
    display: none;
  }

  .hero-stat-item {
    padding: 0;
  }

  .hero-stat-number {
    font-size: 26px;
  }

  .topics-grid {
    grid-template-columns: 1fr;
  }

  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
  }

  .stats-card {
    padding: 20px 16px;
    flex-direction: column;
    text-align: center;
    gap: 12px;
  }

  .stats-number {
    font-size: 22px;
  }

  .section-header h2 {
    font-size: 24px;
  }

  .overview-section,
  .topics-section,
  .importance-section {
    padding: 50px 0;
  }

  .topic-card-inner {
    padding: 28px 24px;
  }

  .importance-card {
    flex-direction: column;
    padding: 24px 20px;
    gap: 12px;
  }

  .importance-number {
    font-size: 32px;
  }

  .importance-quote {
    padding: 28px 24px;
  }

  .importance-quote blockquote {
    font-size: 15px;
    padding-left: 0;
  }

  .quote-icon {
    display: none;
  }

  .overview-image-placeholder {
    height: 160px;
  }

  .overview-image-placeholder i {
    font-size: 48px;
  }
}

@media (max-width: 576px) {
  .container {
    padding: 0 12px;
  }

  .hero-title {
    font-size: 24px;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }

  .stats-card {
    flex-direction: row;
    text-align: left;
    padding: 18px 16px;
  }

  .section-header {
    margin-bottom: 32px;
  }

  .section-header h2 {
    font-size: 20px;
  }

  .topic-card-inner {
    padding: 24px 18px;
  }

  .topic-title {
    font-size: 17px;
  }
}
</style>
