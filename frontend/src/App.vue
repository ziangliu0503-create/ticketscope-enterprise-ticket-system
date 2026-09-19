<script setup>
import { computed, onMounted, ref } from "vue";
import { api } from "./api";
import DashboardView from "./components/DashboardView.vue";
import LoginView from "./components/LoginView.vue";
import TicketDetail from "./components/TicketDetail.vue";
import TicketForm from "./components/TicketForm.vue";
import TicketList from "./components/TicketList.vue";

const activeView = ref("dashboard");
const meta = ref(null);
const currentUser = ref(null);
const loading = ref(api.hasToken());
const error = ref("");
const showCreate = ref(false);
const selectedTicketId = ref(null);
const initialFilters = ref({});
const dashboardRef = ref(null);
const listRef = ref(null);

const roleUi = computed(() => ({
  admin: {
    label: "管理员",
    badge: "全局管理",
    dashboard: "全局运营",
    tickets: "全部工单",
    note: "查看全部工单，负责分派、SLA升级与运营报表。",
  },
  agent: {
    label: "技术人员",
    badge: "处理工作台",
    dashboard: "我的工作台",
    tickets: "待办工单",
    note: "查看待认领及本人负责的工单，完成认领与处理。",
  },
  requester: {
    label: "普通员工",
    badge: "员工服务台",
    dashboard: "我的概览",
    tickets: "我的工单",
    note: "仅查看和创建本人工单，可确认关闭或重新打开。",
  },
}[currentUser.value?.role] || {}));

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
  if (api.hasToken()) initialize();
});
</script>

<template>
  <LoginView v-if="!currentUser && !loading" @logged-in="handleLogin" />
  <div v-else-if="loading" class="full-page-state">正在验证登录信息…</div>
  <div v-else :class="['app-shell', `role-${currentUser.role}`]">
    <aside class="sidebar">
      <div class="brand"><div class="brand-mark">TS</div><div><strong>TicketScope</strong><small>企业服务台</small></div></div>
      <div class="role-identity">
        <span>{{ roleUi.badge }}</span>
        <strong>{{ roleUi.label }}</strong>
        <small>{{ currentUser.name }} · {{ currentUser.department }}</small>
      </div>
      <nav>
        <button :class="{ active: activeView === 'dashboard' }" @click="activeView = 'dashboard'"><span>▦</span>{{ roleUi.dashboard }}</button>
        <button :class="{ active: activeView === 'tickets' }" @click="openList()"><span>☷</span>{{ roleUi.tickets }}</button>
      </nav>
      <div class="sidebar-note"><strong>当前权限范围</strong><p>{{ roleUi.note }}</p></div>
    </aside>

    <main>
      <header class="topbar">
        <div><span class="system-status"></span>系统运行正常 <span class="scope-summary">· 当前为{{ roleUi.label }}视图</span></div>
        <div class="operator"><span><strong>{{ currentUser.name }}</strong><small>{{ meta.role_labels[currentUser.role] }} · {{ currentUser.department }}</small></span><div>{{ currentUser.name.slice(0, 1) }}</div><button class="button text" @click="logout">退出</button></div>
      </header>
      <div v-if="error" class="page state-card error">{{ error }}</div>
      <div v-else class="page">
        <DashboardView v-show="activeView === 'dashboard'" ref="dashboardRef" :current-user="currentUser" @open-list="openList" @create-ticket="showCreate = true" />
        <TicketList v-if="activeView === 'tickets'" ref="listRef" :meta="meta" :current-user="currentUser" :initial-filters="initialFilters" @open-ticket="selectedTicketId = $event" @create-ticket="showCreate = true" />
      </div>
    </main>

    <TicketForm v-if="showCreate && meta" :meta="meta" :current-user="currentUser" @created="handleCreated" @cancel="showCreate = false" />
    <TicketDetail v-if="selectedTicketId && meta" :ticket-id="selectedTicketId" :meta="meta" :current-user="currentUser" @close="selectedTicketId = null" @changed="handleChanged" />
  </div>
</template>
