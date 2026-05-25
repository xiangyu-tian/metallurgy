<template>
  <Header></Header>
  <div class="Search">
    <div class="bgcolor">
      <div class="mb-nav">
        <div class="container">
          <p>
            当前位置： <router-link to="/">首页</router-link> >
            <span>检索框</span>
          </p>
        </div>
      </div>
      <div class="container">
        <div class="Search-item">
          <div class="Search-box wow animate__animated animate__fadeInUp">
            <div class="Search-select">
              <select name="" id="">
                <option value="">全文检索</option>
                <option value="">全文检索</option>
                <option value="">全文检索</option>
                <option value="">全文检索</option>
              </select>
            </div>
            <div class="Search-input">
              <input type="text" placeholder="请输入搜索内容" />
            </div>
            <div class="but">
              <img src="../assets/images/icon-search.png" alt="" />
              <span>搜索</span>
            </div>
          </div>

          <div class="Search-ul pt70 wow animate__animated animate__fadeInUp">
            <ul>
               <li>
                <div class="Search-ul-list">
                    <div class="img">
                          <img src="../assets/images/s1.png" alt="" />
                    </div>
                    <div class="text">
                      <h3>AI</h3>
                    </div>
                </div>
               </li>
               <li>
                <div class="Search-ul-list">
                    <div class="img">
                          <img src="../assets/images/s2.png" alt="" />
                    </div>
                    <div class="text">
                      <h3>氢能源</h3>
                    </div>
                </div>
               </li>
               <li>
                <div class="Search-ul-list">
                    <div class="img">
                          <img src="../assets/images/s3.png" alt="" />
                    </div>
                    <div class="text">
                      <h3>绿色低碳</h3>
                    </div>
                </div>
               </li>
               <li>
                <div class="Search-ul-list">
                    <div class="img">
                          <img src="../assets/images/s4.png" alt="" />
                    </div>
                    <div class="text">
                      <h3>超算</h3>
                    </div>
                </div>
               </li>
               <li>
                <div class="Search-ul-list">
                    <div class="img">
                          <img src="../assets/images/s5.png" alt="" />
                    </div>
                    <div class="text">
                      <h3>数据库</h3>
                    </div>
                </div>
               </li>
               <li>
                <div class="Search-ul-list">
                    <div class="img">
                          <img src="../assets/images/s6.png" alt="" />
                    </div>
                    <div class="text">
                      <h3>化学方程式</h3>
                    </div>
                </div>
               </li>
               <li>
                <div class="Search-ul-list">
                    <div class="img">
                          <img src="../assets/images/s7.png" alt="" />
                    </div>
                    <div class="text">
                      <h3>工具软件</h3>
                    </div>
                </div>
               </li>
               <li>
                <div class="Search-ul-list">
                    <div class="img">
                          <img src="../assets/images/s8.png" alt="" />
                    </div>
                    <div class="text">
                      <h3>计算软件</h3>
                    </div>
                </div>
               </li>
               <li>
                <div class="Search-ul-list">
                    <div class="img">
                          <img src="../assets/images/s9.png" alt="" />
                    </div>
                    <div class="text">
                      <h3>热传递</h3>
                    </div>
                </div>
               </li>
               <li>
                <div class="Search-ul-list">
                    <div class="img">
                          <img src="../assets/images/s10.png" alt="" />
                    </div>
                    <div class="text">
                      <h3>力传递</h3>
                    </div>
                </div>
               </li>
            </ul>
          </div>
        </div>
      </div>
    </div>
    <div class="bgcolor-two pt70 pb150">
        <div class="container">
          <div class="box-title  wow animate__animated animate__fadeInUp">确认基本套餐和附加服务</div>
            <div class="flex-box1 mt25 wow animate__animated animate__fadeInUp">
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
export default {
  name: "MySearch",
  components: {
    Header,
    Footer,
  },
  data() {
    return {};
  },
  methods: {},
  mounted() {},
};
</script>

<style scoped>
.header {
  background: #082a78;
  position: sticky;
}

.box-title {
  font-size: 40px;
  color: #ffffff;
  text-align: center;
}
.Search-item {
  padding-top: 100px;
  padding-bottom: 150px;
}
.Search-box {
  max-width: 730px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 0 auto;
  background-color: #fff;
  border-radius: 5px;
  overflow: hidden;
}
.Search-box .Search-select {
  width: 155px;
  padding-right: 20px;
  position: relative;
}
.Search-box .Search-select::after {
  content: "";
  display: block;
  width: 1px;
  height: 22px;
  background-color: #cccccc;
  position: absolute;
  right: 0;
  top: calc(50% - 11px);
}
.Search-box .Search-select select {
  width: 100%;
  padding-left: 15px;
  border: none;
  outline: none;
  height: 60px;
  font-size: 16px;
  color: #000000;
}
option {
  background-color: #082a78;
  color: #fff;
  line-height: 1.5;
}
.Search-box .Search-input {
  flex: 1;
  padding-left: 20px;
}

.Search-box .Search-input input {
  width: 100%;
  border: none;
  outline: none;
  height: 60px;
  font-size: 16px;
  color: #000;
}
.Search-box .but {
  width: 150px;
  line-height: 60px;
  background-color: #2066fc;
  text-align: center;
  color: #fff;
  font-size: 16px;
  color: #ffffff;
  cursor: pointer;
}
.Search-box .but span {
  display: inline-block;
  vertical-align: middle;
}
.Search-box .but img {
  margin-right: 8px;
}

.Search-ul ul{
  display: flex;
  flex-wrap: wrap;
}
.Search-ul ul li{
  width: 20%;
  text-align: center;
  margin-top: 45px;
}
.Search-ul-list{
  display: block;
  transition: all 0.3s;
}
.Search-ul-list:hover{
  transform: translateY(-8px);
}

.Search-ul-list .img{
  height: 150px;
}
.Search-ul-list .img img{
  height: 100%;
}
.Search-ul-list .text{
  margin-top: 15px;
}
.Search-ul-list .text h3{
  font-size: 18px;
  color: #FFFFFF;
  color: #fff;
}
@media (max-width: 1600px) {
  .box-title {
    font-size: 32px;
  }
  .Search-item{
    padding-top: 80px;
    padding-bottom: 120px;
  }
  .Search-ul-list .img{
    height: 130px;
  }
  .Search-ul-list .text h3{
    font-size: 16px;
  }
  .Search-ul ul li{
    margin-top: 30px;
  }
  .Search-box .Search-input input,.Search-box .Search-select select{
    height: 50px;
  }
  .Search-box .but{
    line-height: 50px;
  }
}

@media (max-width: 1000px) {
  .box-title {
    font-size: 22px;
  }
  .Search-item{
    padding-top: 30px;
    padding-bottom: 30px;
  }
  .Search-box .Search-select{
    width: 110px;
    padding-right: 10px;
  }
   .Search-box .Search-select select{
    padding-left: 10px;
    font-size: 14px;
   }
   .Search-box .but{
    width: 100px;
    font-size: 14px;
   }
   .Search-box .Search-input{
    padding-left: 10px;
   }
   .Search-box .Search-input input{
    font-size: 14px;
   }
   .Search-ul ul li{
    width: 33.33%;
    margin-top: 15px;
   }
   .Search-ul-list .img{
    height: 100px;
   }
   .Search-ul-list .text h3{
    font-size: 14px;
   }
   .Search-ul-list .text{
    margin-top: 10px;
   }
}
</style>