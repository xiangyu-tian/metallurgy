<template>
  <Header></Header>
  <div class="Pro">
    <div class="bgcolor">
      <div class="mb-nav">
        <div class="container">
          <p>
            当前位置： <router-link to="/">首页</router-link> >
            <span>选择产品</span>
          </p>
        </div>
      </div>
      <div class="container">
         <div class="box-title mt50 wow animate__animated animate__fadeInUp">选择产品</div>

         <div class="pro-nav mt50 wow animate__animated animate__fadeInUp">
            <ul>
               <li class="active">
                  <div class="pro-nav-list">
                      <div class="img">
                             <img src="../assets/images/index-one1.png" alt="" />
                      </div>
                      <div class="text">
                          <h3>AI</h3>
                      </div>
                  </div>
               </li>
               <li>
                  <div class="pro-nav-list">
                      <div class="img">
                             <img src="../assets/images/index-one3.png" alt="" />
                      </div>
                      <div class="text">
                          <h3>超算</h3>
                      </div>
                  </div>
               </li>
               <li>
                  <div class="pro-nav-list">
                      <div class="img">
                             <img src="../assets/images/index-one2.png" alt="" />
                      </div>
                      <div class="text">
                          <h3>绿色低碳</h3>
                      </div>
                  </div>
               </li>
               <li>
                  <div class="pro-nav-list">
                      <div class="img">
                             <img src="../assets/images/index-one4.png" alt="" />
                      </div>
                      <div class="text">
                          <h3>氢能源</h3>
                      </div>
                  </div>
               </li>
            </ul>
         </div>
      </div>
      <div class="pro-title">
        <div class="container">
            <p>许可证类型</p>
        </div>
      </div>
    </div>

    <div class="bgcolor pt70 pb150" style="overflow:inherit">
        <div class="container">
             <div class="box-title wow animate__animated animate__fadeInUp">选择许可证类型</div>
            <div class="Pro-type wow animate__animated animate__fadeInUp">
              <ul>
                  <li :class="indexType == 0?'active':''">
                      <div class="Pro-type-list">
                          <h3>Single user</h3>
                          <p class="p1">1个用户从1台注册的计算机访问</p>
                          <div class="Pro-type-tags">
                             <p> <img src="../assets/images/icon-user.png" alt="" /><span>2</span></p>
                             <p> <img src="../assets/images/icon-add2.png" alt="" /><span>5</span></p>
                          </div>
                          <div class="but" @click="SetType(0)">选择许可证</div>

                          <div class="Pro-type-pop">
                            <p>选择的许可证: Single user</p>
                            <p>基础套餐价格: 1240 EUR</p>
                            <p>总计: 1240 EUR</p>
                          </div>
                      </div>
                  </li>
                  <li :class="indexType == 1?'active':''">
                      <div class="Pro-type-list">
                          <h3>网络 S</h3>
                          <p class="p1">来自3个不同地点的最多10个用户</p>
                          <div class="Pro-type-tags">
                             <p> <img src="../assets/images/icon-user.png" alt="" /><span>2</span></p>
                             <p> <img src="../assets/images/icon-add2.png" alt="" /><span>5</span></p>
                          </div>
                          <div class="but" @click="SetType(1)">选择许可证</div>
                           <div class="Pro-type-pop">
                            <p>选择的许可证: 网络 S</p>
                            <p>基础套餐价格: 1240 EUR</p>
                            <p>总计: 1240 EUR</p>
                          </div>
                      </div>
                  </li>
                  <li :class="indexType == 2?'active':''">
                      <div class="Pro-type-list">
                          <h3>网络M</h3>
                          <p class="p1">最多25个用户来自4个不同的地点</p>
                          <div class="Pro-type-tags">
                             <p> <img src="../assets/images/icon-user.png" alt="" /><span>2</span></p>
                             <p> <img src="../assets/images/icon-add2.png" alt="" /><span>5</span></p>
                          </div>
                          <div class="but" @click="SetType(2)">选择许可证</div>
                           <div class="Pro-type-pop">
                            <p>选择的许可证: 网络M</p>
                            <p>基础套餐价格: 1240 EUR</p>
                            <p>总计: 1240 EUR</p>
                          </div>
                      </div>
                  </li>
                  <li :class="indexType == 3?'active':''">
                      <div class="Pro-type-list">
                          <h3>网络L</h3>
                          <p class="p1">最多50个用户来自6个不同地点</p>
                          <div class="Pro-type-tags">
                             <p> <img src="../assets/images/icon-user.png" alt="" /><span>2</span></p>
                             <p> <img src="../assets/images/icon-add2.png" alt="" /><span>5</span></p>
                          </div>
                          <div class="but" @click="SetType(3)">选择许可证</div>
                           <div class="Pro-type-pop">
                            <p>选择的许可证: 网络L</p>
                            <p>基础套餐价格: 1240 EUR</p>
                            <p>总计: 1240 EUR</p>
                          </div>
                      </div>
                  </li>
                  <li :class="indexType == 4?'active':''">
                      <div class="Pro-type-list">
                          <h3>企业</h3>
                          <p class="p1">无限数量的用户，来自无限的地点</p>
                          <div class="Pro-type-tags">
                             <p> <img src="../assets/images/icon-user.png" alt="" /><span>2</span></p>
                             <p> <img src="../assets/images/icon-add2.png" alt="" /><span>5</span></p>
                          </div>
                          <div class="but" @click="SetType(4)">选择许可证</div>
                           <div class="Pro-type-pop">
                            <p>选择的许可证: 企业</p>
                            <p>基础套餐价格: 1240 EUR</p>
                            <p>总计: 1240 EUR</p>
                          </div>
                      </div>
                  </li>
              </ul>
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
  name: "MyPrediction",
  components: {
    Header,
    Footer,
  },
  data() {
    return {
      indexType:0
    }
  },
  methods: {
    SetType(index){
      this.indexType = index
    }
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

.pro-nav ul{
  display: flex;
  flex-wrap: wrap;
}
.pro-nav ul li{
  width: 25%;

}

.pro-nav ul li .pro-nav-list{
  display: block;
  text-align: center;
  width: 100%;
  cursor: pointer;
  position: relative;
}

.pro-nav ul li .pro-nav-list .img{
  width: 188px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
}
.pro-nav ul li .pro-nav-list .text{
  padding: 35px 0;
   position: relative;
  z-index: 1;
}
.pro-nav ul li .pro-nav-list .text h3{
  font-size: 20px;
  color: #FFFFFF;
}

.pro-nav ul li.active .pro-nav-list::after{
  content: '';
  display: block;
  width: 100%;
  height: 67%;
  background-color: #082A78;
  border-radius: 20px;
  position: absolute;
  bottom: 0;
  left: 0;
}
.pro-title{
  width: 100%;
  background: linear-gradient(90deg, rgb(0, 70, 219), rgb(184, 0, 219) 100%);
  font-size: 24px;
  color: #FFFFFF;
  padding: 34px 0;
}
.Pro-type ul{
  display: flex;
  flex-wrap: wrap;
  margin: 0 -30px;
}
.Pro-type ul li{
  width: 20%;
  padding: 0 30px;
  margin-top: 50px;
}
.Pro-type-list{
  display: block;
  position: relative;
}
.Pro-type-list h3{
  font-size: 22px;
  color: #FFFFFF;
}
.Pro-type-list .p1{
  font-size: 16px;
  color: rgba(255,255,255,.7);
  margin-top: 10px;
  min-height: 42px;
}
.Pro-type-list .Pro-type-tags{
  margin-top: 10px;
}
.Pro-type-list .Pro-type-tags p{
  display: inline-block;
  margin-right: 20px;
  font-size: 16px;
  color: #FFFFFF;
  line-height: 20px;
}
.Pro-type-list .Pro-type-tags p img{
  height: 20px;
  vertical-align: bottom;
  margin-right: 5px;
}
.Pro-type-list .but{
  display: inline-block;
  min-width: 130px;
  height: 50px;
  line-height: 50px;
  border: 1px solid #0046db;
  text-align: center;
  margin-top: 10px;
  font-size: 16px;
  color: #0046db;
  background-color: transparent;
  cursor: pointer;
  transition: all 0.5s;
  margin-top: 20px;
}

.Pro-type ul li.active .Pro-type-list .but{
   background-color: #0046db;
  color: #fff;
}
.Pro-type ul li.active .Pro-type-list .Pro-type-pop{
  display: block;
}

.Pro-type-pop{
  display: none;
  padding: 20px;
  border-radius: 20px;
  font-size: 16px;
  color: #FFFFFF;
  background: linear-gradient(90deg, rgb(0, 70, 219), rgb(184, 0, 219) 100%);
  position: absolute;
  bottom: 0;
  left: 0;
  transform: translate(0,calc(100% + 15px));
  z-index: 2;
}
.Pro-type-pop::after{
    content: "";
    position: absolute;
    left: calc(50% - 10px);
    top: -10px;
    width: 0;
    height: 0;
    border-left: 10px solid transparent;
    border-right: 10px solid transparent;
    border-bottom: 10px solid #582aff;
    z-index: 1;
    transition: all 0.5s;
}
.Pro-type-pop p{
  padding: 5px 0;
}

@media (max-width: 1600px) {
  .box-title{
    font-size: 32px;
  }
  .pro-nav ul li .pro-nav-list .img{
    width: 144px;
  }
  .pro-nav ul li .pro-nav-list .text{
    padding: 25px 0;
  }
  .pro-nav ul li .pro-nav-list .text h3{
    font-size: 18px;
  }
  .Pro-type-list h3{
    font-size: 20px;
  }
  .Pro-type-list .p1{
    font-size: 15px;
  }
  .Pro-type-list .Pro-type-tags p img{
    height: 17px;
  }
  .Pro-type-list .Pro-type-tags p{
    font-size: 14px;
  }
  .Pro-type-list .but{
    min-width: 110px;
    height: 42px;
    line-height: 42px;
  }
  .Pro-type-pop{
    font-size: 14px;
  }
   .Pro-type ul{
    margin: 0 -15px;
   }
  .Pro-type ul li{
    padding: 0 15px;
  }
}


@media (max-width: 1000px) {
  .box-title{
    font-size: 22px;
  }
  .pro-nav ul li{
    width: 50%;
    margin: 10px 0;
  }
  .pro-nav ul li .pro-nav-list .img{
    width: 100px;
  }
  .pro-nav ul li .pro-nav-list .text{
    padding: 15px 0;
  }
  .Pro-type ul li{
    width: 50%;
  }
  .pro-title{
    padding: 18px 0;
    font-size: 18px;
  }
  .Pro-type-list h3{
    font-size: 18px;
  }
   .Pro-type ul{
    margin: 0 -5px;
   }
  .Pro-type ul li{
    padding: 0 5px;
  }
  .Pro-type-pop{
    padding: 10px;
  }
  .Pro-type-pop p{
    padding: 2px 0;
  }
}


</style>