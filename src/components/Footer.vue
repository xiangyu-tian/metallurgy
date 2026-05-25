<template>
  <footer class="footer">
    <div class="footer-item">
      <div class="container">
        <div class="footer-logo">
          <img src="../assets/images/logo-icon.png" /> <img src="../assets/images/logo-black.png" />
        </div>
        <div class="footer-box">
          <div class="footer-box-list">
            <h3 class="footer-title">快速链接</h3>
            <div class="footer-box-item">
              <p><router-link to="/">热/动力学数据库与计算</router-link></p>
              <p><router-link to="/">冶金计算流体力学</router-link></p>
              <p><router-link to="/">碳排放核算</router-link></p>
              <p><router-link to="/">过程工艺数据</router-link></p>
              <p><router-link to="/">基础工具软件</router-link></p>
            </div>
          </div>
          <div class="footer-box-list">
            <h3 class="footer-title">联系我们</h3>

            <div class="footer-box-item footer-box-item-img">
              <p><img src="../assets/images/icon-tel.png" alt=""> 0086-755-25691049</p>
              <p><img src="../assets/images/icon-em.png" alt="">info@eastarco.com</p>
              <p><img src="../assets/images/icon-add.png" alt="">
                RM 905,Hongchang Plaza,Shennan Road East, luohu District,
                Shenzhen.
              </p>
            </div>
          </div>
          <div class="footer-box-list">
            <h3 class="footer-title">加入我们</h3>
            <div class="footer-box-em">
              <p>请输入您的邮箱信息</p>
              <div class="footer-search">
                <input type="text" placeholder="E-mail" />
                <div class="but">发送</div>
              </div>

<!--              <div class="footer-link">-->
<!--                <a href="">-->
<!--                  <img src="../assets/images/footer-f1.png" />-->
<!--                </a>-->
<!--                <a href="">-->
<!--                  <img src="../assets/images/footer-f2.png" />-->
<!--                </a>-->
<!--                <a href="">-->
<!--                  <img src="../assets/images/footer-f3.png" />-->
<!--                </a>-->
<!--                <a href="">-->
<!--                  <img src="../assets/images/footer-f4.png" />-->
<!--                </a>-->
<!--              </div>-->
            </div>
          </div>
        </div>
      </div>
    </div>
    <div class="footer-bottom">
      <div class="container">
        <p>Copyright © 2023 北京科技大学. All Rights Reserved.</p>
      </div>
    </div>
  </footer>
</template>

<script>
export default {
  name: "FooterPage",
  props: {},
};
</script>

<!-- Add "scoped" attribute to limit CSS to this component only -->
<style scoped>
.footer {
  background-color: #455467;
}

.footer-item {
  padding-top: 60px;
  padding-bottom: 50px;
}
.footer-logo {
  text-align: center;
}
.footer-logo img {
  height: 55px;
}
.footer-item .footer-box {
  margin-top: 30px;
  display: flex;
  justify-content: space-between;
}

.footer-item .footer-box .footer-box-list {
  max-width: 28%;
}

.footer-item .footer-box .footer-box-list:nth-last-child(1) {
  max-width: 40%;
}

.footer-item .footer-box .footer-box-list .footer-title {
  font-size: 20px;
  color: #ffffff;
  margin-bottom: 20px;
}
.footer-box-item p,
.footer-box-item p a {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.7);
  padding: 10px 0;
}
.footer-box-item p a:hover {
  color: #0071e3;
}
.footer-box-item-img p{
  padding-left: 25px;
  position: relative;
}
.footer-box-item-img p img{
  position: absolute;
  left: 0;
  top: 15px;
}
.footer-box-em p {
  font-size: 16px;
  color: rgba(255, 255, 255, 0.7);
  padding: 10px 0;
}
.footer-box-em .footer-search {
  width: 100%;
  display: flex;
  align-items: center;
  margin-top: 10px;
}
.footer-box-em .footer-search input {
  background-color: rgba(255, 255, 255, 95);
  line-height: 60px;
  border: none;
  outline: none;
  width: 400px;
  padding: 0 15px;
  font-size: 16px;
  color: #929296;
}
.footer-box-em .footer-search .but {
  width: 140px;
  line-height: 60px;
  background-color: #0046db;
  text-align: center;
  font-size: 18px;
  color: #ffffff;
  cursor: pointer;
  transition: all 0.5s;
}
.footer-box-em .footer-search .but:hover {
  opacity: 0.8;
}
.footer-box-em .footer-link a {
  display: inline-block;
  width: 40px;
  height: 40px;
  vertical-align: middle;
  margin-right: 20px;
  margin-top: 35px;
}

.footer-bottom {
  padding: 30px 0;
  border-top: 1px solid rgba(255, 255, 255, 0.1);
  font-size: 14px;
  color: #636364;
  text-align: center;
}
.footer-bottom a {
  font-size: 14px;
  color: #b1b1b1;
}
.footer-bottom a:hover {
  color: #fff;
}

@media (max-width: 1600px) {
  .footer-logo img {
    height: 50px;
  }
  .footer-item .footer-box .footer-box-list .footer-title {
    font-size: 18px;
  }
  .footer-box-em .footer-search input {
    width: 300px;
    height: 50px;
  }
  .footer-box-em .footer-search .but {
    width: 110px;
    line-height: 50px;
    font-size: 16px;
  }
}

@media (max-width: 1000px) {
  .footer-item {
    padding: 25px 0;
  }
  .footer-logo img{
    height: 33px;
  }
  .footer-item .footer-box{
    margin-top: 20px;
  }
  .footer-item .footer-box{
    flex-direction: column;
    margin-top: 0;
  }
  .footer-item .footer-box .footer-box-list{
    width: 100%;
    max-width: 100% !important;
    margin-top: 20px;
  }
  .footer-item .footer-box .footer-box-list .footer-title{
    font-size: 16px;
    margin-bottom: 20px;
    margin-bottom: 15px;
  }
  .footer-box-item p{
    font-size: 14px;
    padding: 5px 0;
    display: inline-block;
    margin-right: 15px;
  }
  .footer-box-item p a{
      font-size: 14px;
  }
  .footer-box-item-img p{
    padding-left: 25px;
    position: relative;
  }
  .footer-box-item-img p img{
    position: absolute;
    left: 0;
    top: 10px;
  }
  .footer-box-em p{
    font-size: 14px;
    padding: 5px 0;
  }
  .footer-box-em .footer-search input{
    height: 45px;
    font-size: 14px;
    flex: 1;
  }
  .footer-box-em .footer-search .but{
    line-height: 45px;
    font-size: 14px;
  }
  .footer-bottom{
    padding: 10px 0;
  }
}
</style>
