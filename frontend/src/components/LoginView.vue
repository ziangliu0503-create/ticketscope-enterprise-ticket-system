<script setup>
import { reactive, ref } from "vue";
import { api } from "../api";

const emit = defineEmits(["logged-in"]);
const form = reactive({ email: "ziang.liu@example.com", password: "Demo123!" });
const loading = ref(false);
const error = ref("");

const accounts = [
  { label: "管理员", email: "ziang.liu@example.com", hint: "全局看板、分配、升级与导出" },
  { label: "技术人员", email: "wang.chen@example.com", hint: "认领与处理本人负责的工单" },
  { label: "普通员工", email: "user1@example.com", hint: "创建并查看本人的工单" },
];

function choose(email) {
  form.email = email;
  form.password = "Demo123!";
}

async function submit() {
  loading.value = true;
  error.value = "";
  try {
    const result = await api.login(form);
    api.setToken(result.token);
    emit("logged-in", result.user);
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <main class="login-page">
    <section class="login-intro">
      <div class="brand large"><div class="brand-mark">TS</div><div><strong>TicketScope</strong><small>企业IT服务台</small></div></div>
      <p class="eyebrow">ROLE-BASED SERVICE DESK</p>
      <h1>让问题受理、处理与复盘形成闭环</h1>
      <p>面向企业内部IT服务管理的作品集项目，包含角色权限、SLA预警、升级机制、运营看板和报表导出。</p>
      <ul><li>员工提交与跟踪</li><li>技术人员认领与处理</li><li>管理员统筹与运营分析</li></ul>
    </section>
    <form class="login-card" @submit.prevent="submit">
      <p class="eyebrow">DEMO LOGIN</p><h2>登录演示系统</h2>
      <div v-if="error" class="alert error">{{ error }}</div>
      <label class="field"><span>邮箱</span><input v-model.trim="form.email" type="email" required /></label>
      <label class="field"><span>密码</span><input v-model="form.password" type="password" required /></label>
      <button class="button primary full" :disabled="loading">{{ loading ? "正在登录…" : "登录" }}</button>
      <div class="demo-accounts"><strong>快速体验不同角色</strong><button v-for="account in accounts" :key="account.email" type="button" @click="choose(account.email)"><span>{{ account.label }}</span><small>{{ account.hint }}</small></button></div>
      <p class="login-note">所有演示账号密码均为 <code>Demo123!</code></p>
    </form>
  </main>
</template>
