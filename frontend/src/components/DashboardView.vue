<script setup>
import { computed, onMounted, ref } from "vue";
import { api } from "../api";
import ChartCard from "./ChartCard.vue";

const props = defineProps({ currentUser: { type: Object, required: true } });
const emit = defineEmits(["open-list", "create-ticket"]);
const dashboard = ref(null);
const loading = ref(true);
const error = ref("");

const statusLabels = { NEW: "待受理", ASSIGNED: "已分配", IN_PROGRESS: "处理中", RESOLVED: "已解决", CLOSED: "已关闭" };
const palette = ["#0f5ba7", "#00a6a6", "#f59e0b", "#ef6c5b", "#64748b", "#7c3aed"];

const roleContent = computed(() => ({
  admin: {
    eyebrow: "ADMIN CONTROL CENTER",
    title: "全局运营中心",
    description: "当前数据覆盖全公司工单，可进行分派、升级、流程管理和报表导出。",
    scope: "全公司数据",
    capabilities: ["查看全部工单", "指定技术负责人", "升级超时工单", "导出运营报表"],
    totalLabel: "全部工单",
    totalHint: "全公司模拟工单",
  },
  agent: {
    eyebrow: "TECHNICIAN WORKSPACE",
    title: "技术人员工作台",
    description: "当前只显示待认领队列和分配给你的工单，请优先处理临期与超时任务。",
    scope: "待认领 + 我的工单",
    capabilities: ["认领待受理工单", "推进处理状态", "填写解决方案", "查看个人处理数据"],
    totalLabel: "我的工作范围",
    totalHint: "待认领及本人负责",
  },
  requester: {
    eyebrow: "EMPLOYEE SERVICE DESK",
    title: "我的服务请求",
    description: "当前只显示你本人提交的工单，你可以创建请求、跟踪进度并确认处理结果。",
    scope: "仅限我的工单",
    capabilities: ["创建服务请求", "跟踪处理进度", "查看解决方案", "关闭或重新打开"],
    totalLabel: "我的工单",
    totalHint: "仅统计本人提交内容",
  },
}[props.currentUser.role]));

function pieOption(items, labels = {}) {
  return {
    color: palette,
    tooltip: { trigger: "item" },
    legend: { bottom: 0, textStyle: { color: "#52606d" } },
    series: [{
      type: "pie",
      radius: ["42%", "68%"],
      center: ["50%", "44%"],
      label: { formatter: "{b}\n{c}" },
      data: items.map((item) => ({ name: labels[item.name] || item.name, value: item.value })),
    }],
  };
}

const categoryOption = computed(() => ({
  color: ["#0f5ba7"],
  tooltip: { trigger: "axis" },
  grid: { left: 76, right: 20, top: 20, bottom: 30 },
  xAxis: { type: "value", splitLine: { lineStyle: { color: "#edf2f7" } } },
  yAxis: { type: "category", data: (dashboard.value?.by_category || []).map((x) => x.name).reverse(), axisLabel: { color: "#52606d" } },
  series: [{ type: "bar", data: (dashboard.value?.by_category || []).map((x) => x.value).reverse(), barWidth: 16, itemStyle: { borderRadius: [0, 5, 5, 0] } }],
}));

const trendOption = computed(() => {
  const rows = dashboard.value?.trend || [];
  return {
    color: ["#0f5ba7", "#00a6a6"],
    tooltip: { trigger: "axis" },
    legend: { data: ["新建", "已解决"], top: 0 },
    grid: { left: 42, right: 20, top: 38, bottom: 40 },
    xAxis: { type: "category", data: rows.map((x) => x.day.slice(5)), axisLabel: { color: "#64748b", rotate: 40 } },
    yAxis: { type: "value", minInterval: 1, splitLine: { lineStyle: { color: "#edf2f7" } } },
    series: [
      { name: "新建", type: "line", smooth: true, data: rows.map((x) => x.created), areaStyle: { opacity: 0.08 } },
      { name: "已解决", type: "line", smooth: true, data: rows.map((x) => x.resolved) },
    ],
  };
});

async function loadDashboard() {
  loading.value = true;
  error.value = "";
  try {
    dashboard.value = await api.getDashboard();
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
}

onMounted(loadDashboard);
defineExpose({ reload: loadDashboard });
</script>

<template>
  <div v-if="loading" class="state-card">正在加载运营数据…</div>
  <div v-else-if="error" class="state-card error">{{ error }}</div>
  <div v-else-if="dashboard" class="dashboard">
    <div class="section-heading">
      <div><p class="eyebrow">{{ roleContent.eyebrow }}</p><h2>{{ roleContent.title }}</h2></div>
      <button class="button ghost" @click="loadDashboard">刷新数据</button>
    </div>

    <section :class="['role-banner', `role-banner-${currentUser.role}`]">
      <div><span class="role-scope">{{ roleContent.scope }}</span><h3>{{ roleContent.description }}</h3></div>
      <div class="capability-list"><span v-for="item in roleContent.capabilities" :key="item">✓ {{ item }}</span></div>
      <button v-if="currentUser.role === 'requester'" class="button primary" @click="emit('create-ticket')">＋ 创建我的工单</button>
      <button v-else class="button ghost" @click="emit('open-list', currentUser.role === 'agent' ? { status: 'NEW' } : {})">{{ currentUser.role === 'admin' ? '进入全部工单' : '查看待认领工单' }}</button>
    </section>

    <div class="metric-grid">
      <button class="metric-card" @click="emit('open-list', {})"><span>{{ roleContent.totalLabel }}</span><strong>{{ dashboard.summary.total }}</strong><small>{{ roleContent.totalHint }}</small></button>
      <button class="metric-card" @click="emit('open-list', { status: 'RESOLVED' })"><span>解决率</span><strong>{{ dashboard.summary.resolution_rate }}%</strong><small>{{ dashboard.summary.resolved }} 条已解决/关闭</small></button>
      <button class="metric-card"><span>SLA达成率</span><strong>{{ dashboard.summary.sla_compliance_rate }}%</strong><small>已解决工单按时完成比例</small></button>
      <button class="metric-card"><span>平均处理时长</span><strong>{{ dashboard.summary.avg_resolution_hours }}h</strong><small>从创建到解决</small></button>
      <button class="metric-card warning" @click="emit('open-list', { sla: 'WARNING' })"><span>即将超时</span><strong>{{ dashboard.summary.warning }}</strong><small>已进入SLA预警区间</small></button>
      <button class="metric-card danger" @click="emit('open-list', { sla: 'OVERDUE' })"><span>超时未完成</span><strong>{{ dashboard.summary.overdue }}</strong><small>{{ dashboard.summary.escalated }} 条已升级处理</small></button>
    </div>

    <div class="chart-grid">
      <ChartCard title="近30天工单趋势" :option="trendOption" />
      <ChartCard title="工单状态分布" :option="pieOption(dashboard.by_status, statusLabels)" />
      <ChartCard title="问题类型分布" :option="categoryOption" />
      <ChartCard v-if="currentUser.role === 'admin'" title="部门工单占比" :option="pieOption(dashboard.by_department)" />
      <ChartCard v-else :title="currentUser.role === 'agent' ? '我的工单优先级' : '我的工单优先级'" :option="pieOption(dashboard.by_priority, { LOW: '低', MEDIUM: '中', HIGH: '高', URGENT: '紧急' })" />
    </div>
    <p class="data-note">数据更新时间：{{ new Date(dashboard.generated_at).toLocaleString() }}。当前展示内容均为模拟数据。</p>
  </div>
</template>
