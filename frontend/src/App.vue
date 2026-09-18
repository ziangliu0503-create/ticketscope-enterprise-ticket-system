<script setup>
import { onMounted, ref } from "vue";
import { api } from "./api";
import DashboardView from "./components/DashboardView.vue";
import LoginView from "./components/LoginView.vue";
import TicketDetail from "./components/TicketDetail.vue";
import TicketForm from "./components/TicketForm.vue";
import TicketList from "./components/TicketList.vue";

const activeView = ref("dashboard");
const meta = ref(null);
const currentUser = ref(null);
const loading = ref(Boolean(localStorage.getItem("ticket_token")));
const error = ref("");
const showCreate = ref(false);
const selectedTicketId = ref(null);
const initialFilters = ref({});
const dashboardRef = ref(null);
const listRef = ref(null);

function openList(filters = {}) {
  initialFilters.value = { ...filters };
  activeView.value = "tickets";
}

async function initialize() {
  loading.value = true;
  error.value = "";
  try {
    meta.value = await api.getMeta();
    currentUser.value = meta.value.current_user;
  } catch (err) {
    api.setToken("");
    meta.value = null;
    currentUser.value = null;
    error.value = err.message;
  } finally {
    loading.value = false;
  }
}

async function handleLogin() {
  await initialize();
  activeView.value = "dashboard";
}

function logout() {
  api.setToken("");
  meta.value = null;
  currentUser.value = null;
  selectedTicketId.value = null;
  showCreate.value = false;
  error.value = "";
}

async function handleCreated(ticket) {
  showCreate.value = false;
  activeView.value = "tickets";
  selectedTicketId.value = ticket.id;
  await listRef.value?.reload();
}

async function handleChanged() {
  await Promise.all([listRef.value?.reload(), dashboardRef.value?.reload()]);
}

onMounted(() => {
  if (localStorage.getItem("ticket_token")) initialize();
});
</script>

<template>
  <LoginView v-if="!currentUser && !loading" @logged-in="handleLogin" />
  <div v-else-if="loading" class="full-page-state">正在验证登录信息…</div>
  <div v-else class="app-shell">
    <aside class="sidebar">
      <div class="brand"><div class="brand-mark">TS</div><div><strong>TicketScope</strong><small>企业服务台</small></div></div>
      <nav>
        <button :class="{ active: activeView === 'dashboard' }" @click="activeView = 'dashboard'"><span>▦</span>运营概览</button>
        <button :class="{ active: activeView === 'tickets' }" @click="openList()"><span>☷</span>工单处理</button>
      </nav>
      <div class="sidebar-note"><strong>角色权限演示</strong><p>{{ meta.role_labels[currentUser.role] }}仅能查看和操作其权限范围内的数据。</p></div>
    </aside>

    <main>
      <header class="topbar">
        <div><span class="system-status"></span>系统运行正常</div>
        <div class="operator"><span><strong>{{ currentUser.name }}</strong><small>{{ meta.role_labels[currentUser.role] }} · {{ currentUser.department }}</small></span><div>{{ currentUser.name.slice(0, 1) }}</div><button class="button text" @click="logout">退出</button></div>
      </header>
      <div v-if="error" class="page state-card error">{{ error }}</div>
      <div v-else class="page">
        <DashboardView v-show="activeView === 'dashboard'" ref="dashboardRef" @open-list="openList" />
        <TicketList v-if="activeView === 'tickets'" ref="listRef" :meta="meta" :current-user="currentUser" :initial-filters="initialFilters" @open-ticket="selectedTicketId = $event" @create-ticket="showCreate = true" />
      </div>
    </main>

    <TicketForm v-if="showCreate && meta" :meta="meta" :current-user="currentUser" @created="handleCreated" @cancel="showCreate = false" />
    <TicketDetail v-if="selectedTicketId && meta" :ticket-id="selectedTicketId" :meta="meta" :current-user="currentUser" @close="selectedTicketId = null" @changed="handleChanged" />
  </div>
</template>
