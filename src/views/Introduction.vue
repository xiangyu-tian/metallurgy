<template>
  <Header></Header>
  <div class="Introduction">
    <div class="bgcolor">
      <div class="mb-nav">
        <div class="container">
          <p>
            当前位置： <router-link to="/">首页</router-link> >
            <span>功能介绍</span>
          </p>
        </div>
      </div>
      <div class="container">
          <div class="Introduction-box">
              <div class="left wow animate__animated animate__fadeInLeft">
                  <h3>绿色低碳钢铁冶金全国重点实验室</h3>
                  <div class="desc">
                    <p>绿色低碳钢铁冶金全国重点实验室（State Key Laboratory of Advanced Metallurgy）代表了我国冶金学科的最高水平，在绿色冶金、智能制造、资源循环等领域具有显著优势：</p>
                    <p><br/></p>
                    <p>· 开发低碳炼铁、冶金渣资源化利用等关键技术；</p>
                    <p>· 在航空航天、新能源等领域的高性能金属材料研发中取得突破；</p>
                    <p>· 多项成果应用于国内大型钢铁企业；</p>
                    <p>· 实验室发表的论文和专利数量居全球冶金领域前列；</p>
                    <p>· 参与制定国家冶金行业标准及“十四五”相关规划；</p>
                    <p>· 冶金过程节能减排与环保技术；</p>
                    <p>· 冶金资源高效利用与循环经济；</p>
                    <p>· 冶金大数据与智能化控制。</p>
                  </div>
                  <div class="butarr">
                  <div class="but">免费试用</div>
                  <div class="but border">了解更多</div>
                </div>
              </div>
              <div class="right wow animate__animated animate__fadeInRight">
                <div class="img" @click="videoPop = true">
                    <img src="../assets/images/video-img.jpeg" alt="">

                    <div class="icon-play">
                       <img src="../assets/images/icon-play.png" alt="">
                    </div>
                </div>
              </div>
          </div>
      </div>
    </div>
    <div class="bgcolor-two pt70 pb150">
        <div class="container">
                <div class="box-title wow animate__animated animate__fadeInUp">确认基本套餐和附加服务</div>
             <div class="flex-box2 mt50 wow animate__animated animate__fadeInUp">

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
            <div class="flex-box1 pt70 wow animate__animated animate__fadeInUp">
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


    <div class="video-pop" v-show="videoPop" @click="videoPop = false">
        <div class="video-pop-box" @click.stop="">
            <video  controls autoplay >
              <source src="../assets/images/video.mp4" type="video/mp4" />
            </video>

            <div class="icon-close" @click="videoPop = false">
                <img src="../assets/images/icon-close.png" alt="">
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
export default {
  name: "MyIntroduction",
  components: {
    Header,
    Footer,
  },
  data() {
    return {
      videoPop:false
    }
  },
  methods: {
    
  },
  mounted() {},
};
</script>

<style scoped>
.header {
  background: #082a78;
  position: sticky;
}

.box-title{
  font-size: 40px;
  color: #FFFFFF;
  text-align: center;
}

.Introduction-box{
  padding-top: 100px;
  padding-bottom: 150px;
  display: flex;
  justify-content: space-between;
}
.Introduction-box .left h3{
  font-size: 32px;
  color: #FFFFFF;
}
.Introduction-box .left .desc{
  font-size: 16px;
  color: rgba(255,255,255,.7);
  margin-top: 30px;
  line-height: 1.8;
}

.Introduction-box .left{
  width: 58%;
  padding-right: 6%;
}

.Introduction-box .right{
  width: 42%;
}
.Introduction-box .right .img img{
  width: 100%;
}
.Introduction-box .right .img{
  position: relative;
}

.Introduction-box .right  .icon-play{
  width: 14.3%;
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%,-50%);
  cursor: pointer;
}

.butarr {
  margin-top: 20px;
}

.butarr .but {
  display: inline-block;
  min-width: 130px;
  height: 50px;
  line-height: 50px;
  border: 1px solid #0046db;
  text-align: center;
  font-size: 16px;
  color: #fff;
  background-color: #0046db;
  cursor: pointer;
  transition: all 0.5s;
  margin-right: 30px;
}
.butarr .but.border {
  background-color: transparent;
  color: #0046db;
}
.butarr .but:hover {
  opacity: 0.8;
  color: #fff;
  background-color: #0046db;
}

@media (max-width: 1600px) {
  .box-title{
    font-size: 32px;
  }
  .Introduction-box{
    padding-top: 80px;
    padding-bottom: 120px;
  }
  .Introduction-box .left h3{
    font-size: 28px;
  }
  .Introduction-box .left .desc{
    margin-top: 20px;
    font-size: 14px;
  }
  .butarr .but{
        min-width: 110px;
        height: 42px;
        line-height: 42px;
        font-size: 14px;
  }
}

@media (max-width: 1000px) {
  .box-title{
    font-size: 22px;
  }
.Introduction-box{
  padding: 30px 0;
  flex-direction: column;
}
.Introduction-box .left{
  width: 100%;
  padding-right: 0;
}
.Introduction-box .right{
  width: 100%;
  margin-top: 20px;
}
.Introduction-box .left h3{
  font-size: 22px;
}
.Introduction-box .left .desc{
  margin-top: 15px;
}
}

</style>

