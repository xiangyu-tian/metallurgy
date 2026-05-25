<template>
  <Header></Header>
  <div class="Prediction">
    <div class="Prediction-nav">
      <ul>
        <li class="active">
          <router-link to="">转炉CFD结构化网格快速生成</router-link>
          <span>|</span>
        </li>
        <li>
          <router-link to="">碳钢</router-link>
          <span>|</span>
        </li>
        <li>
          <router-link to="">不锈钢</router-link>
          <span>|</span>
        </li>
        <li>
          <router-link to="">中合金钢</router-link>
        </li>
      </ul>
    </div>
    <div class="bgcolor">
      <div class="mb-nav">
        <div class="container">
          <p>
            当前位置： <router-link to="/">首页</router-link> >
            <span>转炉CFD结构化网格快速生成</span>
          </p>
        </div>
      </div>
      <div class="Prediction-box">
        <div class="container">
          <div class="Prediction-title">
            转炉CFD结构化网格快速生成
          </div>
          <div class="Prediction-item">
            <!-- 新增导航条 -->
            <div class="Prediction-sidebar">
              <ul>
                <li><router-link to="">介绍</router-link></li>
                <li><router-link to="" @click="selectedType = 'oxygenGun'">氧枪参数</router-link></li>
                <li><router-link to="" @click="selectedType = 'converter'">转炉参数</router-link></li>
                <li><router-link to="">初始化</router-link></li>
                <li><router-link to="" @click="exportData">导出</router-link></li> <!-- 新增导出按钮 -->
              </ul>
            </div>
            <div class="Prediction-sift">
              <!-- 添加一个容器来包裹左侧的输入框，并设置最大高度和滚动条 -->
              <div class="Prediction-sift-box" style="max-height: 500px; overflow-y: auto;">
                <div class="Prediction-sift-list-col">
                  <!-- 根据选中的类型显示不同的输入框 -->
                  <div v-if="selectedType === 'converter' || selectedType === '转炉参数'">
                    <div class="Prediction-sift-list">
                      <p>炉身总高度</p>
                      <input type="number" placeholder="0.00-1.6" v-model="converterDetails.totalHeight" />
                    </div>
                    <div class="Prediction-sift-list">
                      <p>第一段高度</p>
                      <input type="number" placeholder="请输入第一段高度" v-model="converterDetails.firstSegmentHeight" />
                    </div>
                    <div class="Prediction-sift-list">
                      <p>炉身半径</p>
                      <input type="number" placeholder="请输入炉身半径" v-model="converterDetails.bodyRadius" />
                    </div>
                    <div class="Prediction-sift-list">
                      <p>圆角半径</p>
                      <input type="number" placeholder="请输入圆角半径" v-model="converterDetails.cornerRadius" />
                    </div>
                    <div class="Prediction-sift-list">
                      <p>圆角角度</p>
                      <input type="number" placeholder="请输入圆角角度" v-model="converterDetails.cornerAngle" />
                    </div>
                    <div class="Prediction-sift-list">
                      <p>底圆半径</p>
                      <input type="number" placeholder="请输入底圆半径" v-model="converterDetails.baseRadius" />
                    </div>
                    <div class="Prediction-sift-list">
                      <p>底吹孔数量</p>
                      <input type="number" placeholder="0.00-0.31" v-model="converterDetails.blowHoleCount" />
                    </div>
                    <div class="Prediction-sift-list">
                      <p>底吹孔类型</p>
                      <div class="segmented-control">
                        <button :class="{ active: boBlowType === 'arc' }" @click="boBlowType = 'arc'">圆弧</button>
                        <button :class="{ active: boBlowType === 'straight' }" @click="boBlowType = 'straight'">直线</button>
                      </div>
                    </div>
                    <div v-if="boBlowType === 'arc'">
                      <div class="Prediction-sift-list">
                        <p>弧线条数</p>
                        <input type="number" v-model="arcDetails.arcCount" placeholder="请输入弧线条数" />
                      </div>
                      <div class="Prediction-sift-list">
                        <p>弧半径</p>
                        <input type="number" v-model="arcDetails.arcRadius" placeholder="请输入弧半径" />
                      </div>
                      <div class="Prediction-sift-list">
                        <p>角度</p>
                        <input type="number" v-model="arcDetails.angle" placeholder="请输入角度" />
                      </div>
                      <div class="Prediction-sift-list">
                        <p>底吹孔半径</p>
                        <input type="number" v-model="arcDetails.boBlowRadius" placeholder="请输入底吹孔半径" />
                      </div>
                    </div>
                    <div v-else-if="boBlowType === 'straight'">
                      <div class="Prediction-sift-list">
                        <p>直线总数</p>
                        <input type="number" v-model="straightDetails.straightCount" placeholder="请输入直线总数" />
                      </div>
                      <div class="Prediction-sift-list">
                        <p>直线X坐标</p>
                        <input type="number" v-model="straightDetails.straightX" placeholder="请输入直线X坐标" />
                      </div>
                      <div class="Prediction-sift-list">
                        <p>直线Y坐标</p>
                        <input type="number" v-model="straightDetails.straightY" placeholder="请输入直线Y坐标" />
                      </div>
                      <div class="Prediction-sift-list">
                        <p>底吹孔半径</p>
                        <input type="number" v-model="straightDetails.boBlowRadius" placeholder="请输入底吹孔半径" />
                      </div>
                    </div>
                  </div>
                  <div v-else-if="selectedType === 'oxygenGun' || selectedType === '氧枪参数'">
                    <!-- 添加氧枪相关的输入框 -->
                    <div class="Prediction-sift-list">
                      <p>氧枪数量</p>
                      <input type="number" placeholder="0.00-11.9" v-model="oxygenGunDetails.gunCount" />
                    </div>
                    <div class="Prediction-sift-list">
                      <p>氧枪倾斜角度</p>
                      <input type="number" v-model="oxygenGunDetails.tiltAngle" placeholder="请输入氧枪倾斜角度" />
                    </div>
                    <div class="Prediction-sift-list">
                      <p>是否有中心孔</p>
                      <div class="segmented-control">
                        <button :class="{ active: oxygenGunDetails.hasCenterHole === true }" @click="oxygenGunDetails.hasCenterHole = true">是</button>
                        <button :class="{ active: oxygenGunDetails.hasCenterHole === false }" @click="oxygenGunDetails.hasCenterHole = false">否</button>
                      </div>
                    </div>
                    <!-- 新增条件判断，当 oxygenGunDetails.hasCenterHole 为 true 时显示这些输入框 -->
                    <div v-if="oxygenGunDetails.hasCenterHole">
                      <div class="Prediction-sift-list">
                        <p>孔半径</p>
                        <input type="number" v-model="oxygenGunDetails.holeRadius" placeholder="请输入孔半径" />
                      </div>
                      <div class="Prediction-sift-list">
                        <p>一段氧枪半径</p>
                        <input type="number" v-model="oxygenGunDetails.firstSegmentHeightRadius" placeholder="请输入一段氧枪高度半径" />
                      </div>
                      <div class="Prediction-sift-list">
                        <p>二段氧枪半径</p>
                        <input type="number" v-model="oxygenGunDetails.secondSegmentHeightRadius" placeholder="请输入二段氧枪高度半径" />
                      </div>
                      <div class="Prediction-sift-list">
                        <p>三段氧枪半径</p>
                        <input type="number" v-model="oxygenGunDetails.thirdSegmentHeightRadius" placeholder="请输入三段氧枪高度半径" />
                      </div>
                      <div class="Prediction-sift-list">
                        <p>一段氧枪高度</p>
                        <input type="number" v-model="oxygenGunDetails.firstSegmentHeight" placeholder="请输入一段氧枪高度" />
                      </div>
                      <div class="Prediction-sift-list">
                        <p>二段氧枪高度</p>
                        <input type="number" v-model="oxygenGunDetails.secondSegmentHeight" placeholder="请输入二段氧枪高度" />
                      </div>
                      <div class="Prediction-sift-list">
                        <p>三段氧枪高度</p>
                        <input type="number" v-model="oxygenGunDetails.thirdSegmentHeight" placeholder="请输入三段氧枪高度" />
                      </div>
                    </div>
                    <div class="Prediction-sift-list">
                      <p>氧枪圈数</p>
                      <input type="number" v-model="oxygenGunDetails.gunCount" placeholder="请输入氧枪圈数" />
                    </div>
                    <div v-for="(circle, index) in oxygenGunDetails.circles" :key="circle.id" class="Prediction-sift-list">
                      <p>{{ index + 1 }}</p>
                      <div class="Prediction-sift-list-column">
                        <div class="Prediction-sift-list">
                          <p>孔半径</p>
                          <input type="number" v-model="circle.holeRadius" placeholder="请输入孔半径" />
                        </div>
                        <div class="Prediction-sift-list">
                          <p>一段氧枪半径</p>
                          <input type="number" v-model="circle.firstSegmentHeightRadius" placeholder="请输入一段氧枪高度半径" />
                        </div>
                        <div class="Prediction-sift-list">
                          <p>二段氧枪半径</p>
                          <input type="number" v-model="circle.secondSegmentHeightRadius" placeholder="请输入二段氧枪高度半径" />
                        </div>
                        <div class="Prediction-sift-list">
                          <p>三段氧枪半径</p>
                          <input type="number" v-model="circle.thirdSegmentHeightRadius" placeholder="请输入三段氧枪高度半径" />
                        </div>
                        <div class="Prediction-sift-list">
                          <p>一段氧枪高度</p>
                          <input type="number" v-model="circle.firstSegmentHeight" placeholder="请输入一段氧枪高度" />
                        </div>
                        <div class="Prediction-sift-list">
                          <p>二段氧枪高度</p>
                          <input type="number" v-model="circle.secondSegmentHeight" placeholder="请输入二段氧枪高度" />
                        </div>
                        <div class="Prediction-sift-list">
                          <p>三段氧枪高度</p>
                          <input type="number" v-model="circle.thirdSegmentHeight" placeholder="请输入三段氧枪高度" />
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div class="Prediction-butarr">
                <div class="but">重置</div>
                <div class="but border" @click="importPresetData">导入</div>
              </div>
            </div>
            <div class="Prediction-content">
              <div class="structure">
                <div>
                  <div class="image-container">
                    <div class="image-box">
                      <img src="../assets/images/hole_y.png" alt="">
                      <div class="image-label">1</div>
                    </div>
                  </div>
                </div>
                <div>
                  <div class="image-container">
                    <div class="image-box">
                      <img src="../assets/images/hole_x.png" alt="">
                      <div class="image-label">2</div>
                    </div>
                  </div>
                </div>
              </div>
              <div class="Prediction-map" id="Prediction-map"></div>
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="bgcolor-two pt70 pb150">
      <div class="container">
        <div class="flex-box1 wow animate__animated animate__fadeInUp">
          <ul>
            <li>
              <div class="flex-box1-list">
                <div class="icon">
                  <img src="../assets/images/icon-flex1.png" alt="">
                </div>
                <div class="text">
                  <h3 class="title">扩展范围</h3>
                  <div class="tags">
                    <span>应力应变</span>
                    <span>蠕变和断裂</span>
                    <span>疲劳数据</span>
                    <span>成形性图表</span>
                  </div>
                  <div class="but">选择附加组件</div>
                </div>
              </div>
            </li>
            <li>
              <div class="flex-box1-list">
                <div class="icon">
                  <img src="../assets/images/icon-flex2.png" alt="">
                </div>
                <div class="text">
                  <h3 class="title">材料控制台</h3>
                  <div class="tags">
                    <span>材料清单</span>
                    <span>导出到CAx</span>
                    <span>分享报告</span>
                    <span>比较工具</span>
                  </div>
                  <div class="but">选择附加组件</div>
                </div>
              </div>
            </li>
            <li>
              <div class="flex-box1-list">
                <div class="icon">
                  <img src="../assets/images/icon-flex3.png" alt="">
                </div>
                <div class="text">
                  <h3 class="title">合规</h3>
                  <div class="tags">
                    <span>>300个全球法规</span>
                    <span>豁免信息</span>
                    <span>物质数据</span>
                    <span>更新的规定</span>
                  </div>
                  <div class="but">选择附加组件</div>
                </div>
              </div>
            </li>
            <li>
              <div class="flex-box1-list">
                <div class="icon">
                  <img src="../assets/images/icon-flex4.png" alt="">
                </div>
                <div class="text">
                  <h3 class="title">AI</h3>
                  <div class="tags">
                    <span>材料识别</span>
                    <span>专利算法</span>
                    <span>专家模块</span>
                    <span>光谱仪集成</span>
                  </div>
                  <div class="but">选择附加组件</div>
                </div>
              </div>
            </li>
          </ul>
        </div>
        <div class="flex-box2 mt100 wow animate__animated animate__fadeInUp">

          <ul >
            <li>
              <div class="flex-box2-list">
                <div class="title">
                  <img src="../assets/images/icon-flex5.png" alt="">
                  <h3>总搜索</h3>
                </div>
              </div>
            </li>
            <li>
              <div class="flex-box2-list">
                <div class="title">
                  <img src="../assets/images/icon-flex6.png" alt="">
                  <h3>数据加</h3>
                </div>
              </div>
            </li>
            <li>
              <div class="flex-box2-list">
                <div class="title">
                  <img src="../assets/images/icon-flex7.png" alt="">
                  <h3>总搜索</h3>
                </div>
              </div>
            </li>
            <li>
              <div class="flex-box2-list">
                <div class="title">
                  <img src="../assets/images/icon-flex8.png" alt="">
                  <h3>跟踪器</h3>
                </div>
              </div>
            </li>
          </ul>

          <div class="flex-box2-p">
            <ul>
              <li>
                <p>> 540,000种材料</p>
              </li>
              <li>
                <p>材料等效性</p>
              </li>
              <li>
                <p>80+标准</p>
              </li>
              <li>
                <p>化学成分</p>
              </li>
              <li>
                <p>机械性能</p>
              </li>
              <li>
                <p>物理特性</p>
              </li>
              <li>
                <p>热处理</p>
              </li>
              <li>
                <p>金相学</p>
              </li>
              <li>
                <p>焊接和钎焊</p>
              </li>
              <li>
                <p>腐蚀和老化</p>
              </li>
              <li>
                <p>涂层与摩擦学</p>
              </li>
              <li>
                <p>全球供应商</p>
              </li>
            </ul>

          </div>

        </div>
      </div>
    </div>
  </div>
  <Footer></Footer>
</template>
<script>
// @ is an alias to /src
import Header from "@/components/Header.vue";
import Footer from "@/components/Footer.vue";
import * as echarts from "echarts";
// 引入axios库
import axios from "axios";
// 引入FileSaver库
import { saveAs } from 'file-saver';

export default {
  name: "MyPrediction",
  components: {
    Header,
    Footer,
  },
  data() {
    return {
      selectedType: 'converter', // 默认选中转炉
      boBlowType: 'arc', // 默认选中圆弧
      arcDetails: { // 新增数据绑定
        arcCount: '',
        arcRadius: '',
        angle: '',
        boBlowRadius: ''
      },
      straightDetails: { // 新增数据绑定
        straightCount: '',
        straightX: '',
        straightY: '',
        boBlowRadius: ''
      },
      oxygenGunDetails: { // 新增数据绑定
        gunCount: '',
        circles: []
      },
      converterDetails: { // 新增数据绑定
        totalHeight: '',
        firstSegmentHeight: '',
        bodyRadius: '',
        cornerRadius: '',
        cornerAngle: '',
        baseRadius: '',
        blowHoleCount: ''
      }
    };
  },
  methods: {
    // 右侧月用户数据
    PredictionMap(box) {
      // 基于准备好的dom，初始化echarts实例
      let myChart = echarts.init(document.getElementById(box));

      let option = {
        tooltip: {
          trigger: "axis",
          axisPointer: {
            type: "cross",
          },
          formatter: function (param) {
            return `${param[0].marker}${param[0].seriesName}:${param[0].data}<br />
            ${param[1].marker}${param[1].seriesName}:${param[1].data}<br />
            ${param[2].marker}${param[2].seriesName}:${param[2].data}<br />
            ${param[3].marker}${param[3].seriesName}:${param[3].data}<br />
            ${param[4].marker}${param[4].seriesName}:${param[4].data}<br />
            ${param[5].marker}${param[5].seriesName}:${param[5].data}<br />
            `;
          },
        },
        legend: {
          data: ["Ac1", "Psupper", "Pslower","Pfupper","Pflower","Ms"],
          textStyle: {
            color: "#A5D2EF",
            fontWeight: "normal",
            fontSize: 14,
          },
        },
        grid: {
          left: "1%",
          top: "13%",
          right: "3%",
          bottom: "3%",
          containLabel: true,
        },
        xAxis: {
          type: "category",
          boundaryGap: false,
          splitLine: {
            show: false,
          },
          axisTick: {
            show: false,
          },
          axisLine: {
            show: false,
            lineStyle: {
              color: "rgba(255,255,255,.6)",
            },
          },
          data: ["0.1", "1", "10", "100", "1000", "10000", "100000"],
        },
        yAxis: {
          type: "value",
          splitLine: {
            show: true,
            lineStyle: {
              type: "dashed",
              color: "#fff",
              opacity: 0.1,
            },
          },
          axisLine: {
            lineStyle: {
              color: "rgba(255,255,255,.6)",
            },
          },
        },
        series: [
          {
            name: 'Ac1',
            data: [860.6, 860.3, 850.6, 860.90, 861.4, 862.3, 860.6],
            type: "line",
            smooth: true,
            color: "#000000",
          },
          {
            name: 'Psupper',
            data: [724.8, 724.9, 734.8, 725.8, 724.4, 724.8, 724.8],
            type: "line",
            smooth: true,
            color: "#ffff00",
          },
          {
            name: 'Pslower',
            data: [617.5, 618.5, 616.5, 615.8, 558.5, 620.9, 617.5],
            type: "line",
            smooth: true,
            color: "#f47920",
          },
          {
            name: 'Pfupper',
            data: [703.5, 703.5, 703.5, 703.5, 703.5, 703.5, 703.5],
            type: "line",
            smooth: true,
            color: "#ff00e6",
          },
          {
            name: 'Pflower',
            data: [681.5, 681.5, 681.5, 681.5, 681.5, 681.5, 681.5],
            type: "line",
            smooth: true,
            color: "#ff0000",
          },
          {
            name: 'Ms',
            data: [195.8, 185.8, 205.8, 195.8, 130.8, 195.8, 175.8],
            type: "line",
            smooth: true,
            color: "#0033ff",
          },
        ],
      };

      // 使用刚指定的配置项和数据显示图表。
      // myChart.setOption(option);
      // window.addEventListener("resize", () => {
      //   if (myChart) {
      //     myChart.resize();
      //   }
      // });
    },
    updateCircles() {
      const count = parseInt(this.oxygenGunDetails.gunCount, 10);
      if (count > 0) {
        this.oxygenGunDetails.circles = Array.from({ length: count }, (_, i) => ({
          id: i + 1,
          holeRadius: 1,
          firstSegmentHeightRadius: 1,
          secondSegmentHeightRadius: 1,
          thirdSegmentHeightRadius: 1,
          firstSegmentHeight: 1,
          secondSegmentHeight: 1,
          thirdSegmentHeight: 1
        }));
      } else {
        this.oxygenGunDetails.circles = [];
      }
    },
    // 新增方法，用于从presetData.json导入预设数据
    importPresetData() {
      axios.get('/assets/presetData.json')
          .then(response => {
            const data = response.data;
            if (this.selectedType === 'converter' || this.selectedType === '转炉参数') {
              this.arcDetails = data.converter.arcDetails;
              this.straightDetails = data.converter.straightDetails;
              this.boBlowType = data.converter.boBlowType;
              this.converterDetails = data.converter.converterDetails;
              this.selectedType = 'converter';
            } else if (this.selectedType === 'oxygenGun' || this.selectedType === '氧枪参数') {
              this.oxygenGunDetails = data.oxygenGun;
              this.selectedType = 'oxygenGun';
              this.updateCircles(); // 更新氧枪圈数
            }
          })
          .catch(error => {
            console.error('Error fetching preset data:', error);
          });
    },
    // 新增方法，用于初始化
    initialize() {
      axios.post('http://localhost:3001/run-script')
        .then(response => {
          console.log('脚本执行成功:', response.data);
        })
        .catch(error => {
          console.error('脚本执行失败:', error);
        });
    },
    // 新增方法，用于导出数据到JSON文件
    exportData() {
      const data = {
        converter: {
          arcDetails: this.arcDetails,
          straightDetails: this.straightDetails,
          boBlowType: this.boBlowType,
          converterDetails: this.converterDetails
        },
        oxygenGun: this.oxygenGunDetails
      };
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json;charset=utf-8' });
      saveAs(blob, '/D:/bkdwghf/src/assets/presetData.json'); // 确保文件保存在当前项目目录下的 bkdwghf 文件夹中
    }
  },
  watch: {
    'oxygenGunDetails.gunCount': 'updateCircles'
  },
  mounted() {
    this.PredictionMap("Prediction-map");
    // 添加日志信息，确认图片路径是否正确
    console.log('hole_y.png path:', require('../assets/images/hole_y.png'));
    console.log('hole_x.png path:', require('../assets/images/hole_x.png'));
  },
};
</script>

<style scoped>
.header {
  background: #082a78;
  position: sticky;
}

.Prediction-nav {
  background-color: #011540;
  text-align: center;
}
.Prediction-nav ul li {
  display: inline-block;
}
.Prediction-nav ul li span {
  vertical-align: middle;
  margin: 0 50px;
  color: #fff;
  line-height: 1;
  font-size: 14px;
}
.Prediction-nav ul li a {
  display: inline-block;
  font-size: 16px;
  color: #ffffff;
  line-height: 60px;
  vertical-align: middle;
  border-bottom: 2px solid transparent;
}
.Prediction-nav ul li.active a {
  color: #2066fc;
  font-weight: bold;
  border-color: #2066fc;
}
.Prediction-box {
  margin-top: 45px;
}
.Prediction-box .Prediction-title {
  font-size: 28px;
  color: #ffffff;
  font-weight: bold;
  text-align: center;
}
.Prediction-item {
  margin-top: 30px;
  padding-bottom: 135px;
  display: flex;
}


.Prediction-sidebar {
  width: 20%;
  padding-right: 20px;
  height: 500px; /* 设置高度为500px */
  display: flex; /* 使用Flexbox布局 */
  flex-direction: column; /* 设置为竖向布局 */
  justify-content: space-around; /* 使内容竖向均匀分布 */
  align-items: center; /* 使内容水平居中 */
  padding: 50px 0; /* 设置上下留白为50px */
}

.Prediction-sidebar ul {
  list-style-type: none;
  padding: 0;
}

.Prediction-sidebar ul li {
  margin-bottom: 10px;
}

.Prediction-sidebar ul li a {
  display: block;
  padding: 10px;
  background-color: #0046db;
  color: #fff;
  text-decoration: none;
  border-radius: 5px;
  transition: background-color 0.3s;
  text-align: center; /* 新增：使文字居中 */
}

.Prediction-sidebar ul li a:hover {
  background-color: #003399;
}

.Prediction-sift {
  width: 40%; /* 修改宽度以适应新的导航条 */
}

.Prediction-sift .title {
  font-size: 16px;
  color: #ffffff;
  margin-bottom: 20px;
}

.Prediction-sift-box {
  display: flex;
  max-height: 500px; /* 设置最大高度 */
  overflow-y: auto; /* 添加垂直滚动条 */
  padding-right: 10px; /* 增加右侧内边距，使输入框和滚动条之间有间距 */
}

.Prediction-sift-list-col {
  flex: 1;
}

.Prediction-sift-list {
  display: flex;
  align-items: center;
  margin: 10px 0;
}

.Prediction-sift-list p {
  width: 110px;
  font-size: 16px;
  color: #ffffff;
}

.Prediction-sift-list input {
  flex: 1;
  height: 50px;
  border: 1px solid #264a7e;
  background-color: #002a67;
  padding: 0 20px;
  outline: none;
  color: #fff;
  font-size: 16px;
  width: 100%;
}

.Prediction-sift-list select {
  flex: 1;
  height: 50px;
  border: 1px solid #264a7e;
  background-color: #002a67;
  padding: 0 20px;
  outline: none;
  color: #fff;
  font-size: 16px;
  width: 100%;
}

.Prediction-butarr {
  padding-left: 110px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.Prediction-butarr .but {
  width: calc(50% - 10px);
  height: 50px;
  line-height: 50px;
  border: 1px solid #0046db;
  text-align: center;
  margin-top: 10px;
  font-size: 16px;
  color: #fff;
  background-color: #0046db;
  cursor: pointer;
  transition: all 0.5s;
}
.Prediction-butarr .but.border {
  background-color: transparent;
  color: #0046db;
}
.Prediction-butarr .but:hover {
  opacity: 0.8;
  color: #fff;
  background-color: #0046db;

}

.Prediction-content {
  width: 100%; /* 修改宽度为100% */
  margin-left: 0; /* 移除左边距 */
  display: flex;
  justify-content: center; /* 修改为居中 */
  align-items: center;
}
.Prediction-content .title {
  font-size: 16px;
  color: #ffffff;
  margin-bottom: 20px;
}
.Prediction-map {
  width: 100%;
  height: 500px;
}
.Prediction-desc {
  font-size: 18px;
  color: rgba(255, 255, 255, 0.7);
  margin-top: 0;
}

.segmented-control {
  display: flex;
  margin-top: 10px;
}

.segmented-control button {
  padding: 10px 20px;
  border: 1px solid #264a7e;
  background-color: #002a67;
  color: #fff;
  font-size: 16px;
  cursor: pointer;
  transition: all 0.3s;
}

.segmented-control button.active {
  background-color: #0046db;
  border-color: #0046db;
}

.segmented-control button:hover {
  opacity: 0.8;
}

@media (max-width: 1600px) {
  .Prediction-content{
    width: calc(100% - 340px);
    padding-left: 40px;
    display: flex;
    justify-content: flex-end;
    align-items: center;
  }
  .Prediction-sift{
    width: 33.33%;
  }
  .Prediction-sift-list p{
    font-size: 14px;
    width: 100px;
  }
  .Prediction-sift-list input{
    height: 42px;
    font-size: 14px;
    width: 100px;
  }
  .Prediction-box .Prediction-title{
    font-size: 24px;
  }
  .Prediction-map{
    height: 400px;
  }
  .Prediction-desc{
    font-size: 16px;
  }
  .table table tr th,.table table tr td{
    font-size: 14px;
  }
  .Prediction-butarr{
    padding-left: 100px;
  }
  .Prediction-butarr .but{
    line-height: 40px;
    height: 40px;
  }
}

@media (max-width: 1000px) {
  .Prediction-nav ul li a{
    line-height: 42px;
    font-size: 14px;
  }
  .Prediction-nav ul li span{
    margin: 0 15px;
  }
  .Prediction-box .Prediction-title{
    font-size: 18px;
  }
  .Prediction-box{
    margin-top: 25px;
  }
  .Prediction-item{
    flex-direction: column;
    padding-bottom: 30px;
  }
  .Prediction-sift{
    width: 100%;
  }
  .Prediction-sift-list input{
    width: 80px;
  }
  .Prediction-content{
    width: 100%;
    padding-left: 0;
    margin-top: 15px;
    display: flex;
    justify-content: flex-end;
    align-items: center;
  }
  .Prediction-butarr{
    padding-left: 0;
  }
  .Prediction-desc{
    font-size: 14px;
  }
  .Prediction-table{
    margin-top: 0px;
  }
  .Prediction-content .title{
    font-size: 12px;
  }
}

.structure {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-top: -220px;
  border: 4px solid #fff; /* 增加边框宽度 */
  border-top-width: 2px; /* 上下边框更细 */
  border-bottom-width: 2px;
  padding: 10px;
  border-radius: 5px;
  width: calc(100% + 860px); /* 调整宽度 */
  position: relative;
  left: 60px; /* 调整左边距 */
  margin-right: 20px; /* 添加右边距 */
}

.image-container {
  position: relative;
  display: inline-block;
  width: 100%; /* 增加宽度 */
}

.structure > div {
  margin: 10px; /* 修改：调整间距 */
  width: 45%; /* 修改：调整宽度 */
  height: auto; /* 保持高度自适应 */
}

.structure > div img {
  width: 100%; /* 修改：图片宽度自适应 */
  height: auto; /* 图片高度自适应 */
}

.image-container {
  position: relative;
  display: inline-block;
}

.image-box {
  position: relative;
  padding: 5px; /* 添加：内边距 */
}

.image-label {
  position: absolute;
  bottom: -10px; /* 添加：标签位置 */
  left: 50%;
  transform: translateX(-50%);
  color: #fff;
  font-size: 16px;
  background-color: #0046db; /* 添加：背景色 */
  padding: 2px 5px;
  border-radius: 3px; /* 添加：圆角 */
}

.Prediction-sift-list-column {
  display: flex;
  flex-direction: column;
}

/* 修改滚动条样式 */
.Prediction-sift-box::-webkit-scrollbar {
  width: 8px; /* 滚动条宽度 */
}

.Prediction-sift-box::-webkit-scrollbar-track {
  background: rgba(255, 255, 255, 0.1); /* 滚动条轨道背景色 */
}

.Prediction-sift-box::-webkit-scrollbar-thumb {
  background: rgba(255, 255, 255, 0.3); /* 滚动条滑块背景色 */
  border-radius: 4px; /* 滚动条滑块圆角 */
}

.Prediction-sift-box::-webkit-scrollbar-thumb:hover {
  background: rgba(255, 255, 255, 0.5); /* 滚动条滑块悬停背景色 */
}
</style>