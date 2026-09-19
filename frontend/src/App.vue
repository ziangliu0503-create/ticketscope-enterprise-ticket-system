<script setup>
import { onMounted, ref } from "vue";
import { api } from "./api";
import DashboardView from "./components/DashboardView.vue";
import TicketDetail from "./components/TicketDetail.vue";
import TicketForm from "./components/TicketForm.vue";
import TicketList from "./components/TicketList.vue";

const activeView = ref("dashboard");
const meta = ref(null);
const loading = ref(true);
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

async function handleCreated(ticket) {
  showCreate.value = false;
  activeView.value = "tickets";
  selectedTicketId.value = ticket.id;
  await listRef.value?.reload();
}

async function handleChanged() {
  await Promise.all([listRef.value?.reload(), dashboardRef.value?.reload()]);
}

onMounted(async () => {
  try {
    meta.value = await api.getMeta();
  } catch (err) {
    error.value = `${err.message}。请确认 Flask 后端已在 5000 端口运行。`;
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand"><div class="brand-mark">TS</div><div><strong>TicketScope</strong><small>企业服务台</small></div></div>
      <nav>
        <button :class="{ active: activeView === 'dashboard' }" @click="activeView = 'dashboard'"><span>▦</span>运营概览</button>
        <button :class="{ active: activeView === 'tickets' }" @click="openList()"><span>☷</span>工单处理</button>
      </nav>
      <div class="sidebar-note"><strong>演示项目</strong><p>数据均为程序生成的模拟数据，用于展示需求分析、接口联调和运营指标设计。</p></div>
    </aside>

    <main>
      <header class="topbar"><div><span class="system-status"></span>系统运行正常</div><div class="operator"><span>演示管理员</span><div>刘</div></div></header>
      <div v-if="loading" class="page state-card">正在初始化系统…</div>
      <div v-else-if="error" class="page state-card error">{{ error }}</div>
      <div v-else class="page">
        <DashboardView v-show="activeView === 'dashboard'" ref="dashboardRef" @open-list="openList" />
        <TicketList v-if="activeView === 'tickets'" ref="listRef" :meta="meta" :initial-filters="initialFilters" @open-ticket="selectedTicketId = $event" @create-ticket="showCreate = true" />
      </div>
    </main>

    <TicketForm v-if="showCreate && meta" :meta="meta" @created="handleCreated" @cancel="showCreate = false" />
    <TicketDetail v-if="selectedTicketId && meta" :ticket-id="selectedTicketId" :meta="meta" @close="selectedTicketId = null" @changed="handleChanged" />
  </div>
</template>

