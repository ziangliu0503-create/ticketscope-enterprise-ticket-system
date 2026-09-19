<script setup>
import { onMounted, reactive, ref, watch } from "vue";
import { api } from "../api";

const props = defineProps({ meta: { type: Object, required: true }, initialFilters: { type: Object, default: () => ({}) } });
const emit = defineEmits(["open-ticket", "create-ticket"]);
const tickets = ref([]);
const total = ref(0);
const loading = ref(true);
const error = ref("");
const filters = reactive({ search: "", status: "", priority: "", department: "", category: "", page: 1, per_page: 15, ...props.initialFilters });
const statusLabels = { NEW: "待受理", ASSIGNED: "已分配", IN_PROGRESS: "处理中", RESOLVED: "已解决", CLOSED: "已关闭" };
const priorityLabels = { LOW: "低", MEDIUM: "中", HIGH: "高", URGENT: "紧急" };
let debounce;

async function loadTickets() {
  loading.value = true;
  error.value = "";
  try {
    const payload = await api.getTickets(filters);
    tickets.value = payload.items;
    total.value = payload.total;
  } catch (err) {
    error.value = err.message;
  } finally {
    loading.value = false;
  }
}

function resetFilters() {
  Object.assign(filters, { search: "", status: "", priority: "", department: "", category: "", page: 1 });
}

function changePage(delta) {
  filters.page = Math.max(1, filters.page + delta);
}

watch(filters, () => {
  clearTimeout(debounce);
  debounce = setTimeout(loadTickets, 180);
}, { deep: true });
watch(() => props.initialFilters, (value) => Object.assign(filters, value, { page: 1 }), { deep: true });
onMounted(loadTickets);
defineExpose({ reload: loadTickets });
</script>

<template>
  <div>
    <div class="section-heading"><div><p class="eyebrow">TICKET WORKSPACE</p><h2>工单处理</h2></div><button class="button primary" @click="emit('create-ticket')">＋ 创建工单</button></div>
    <section class="panel filters">
      <label class="search-box"><span>⌕</span><input v-model="filters.search" placeholder="搜索工单编号、标题或描述" /></label>
      <select v-model="filters.status"><option value="">全部状态</option><option v-for="item in meta.statuses" :key="item" :value="item">{{ statusLabels[item] }}</option></select>
      <select v-model="filters.priority"><option value="">全部优先级</option><option v-for="item in meta.priorities" :key="item" :value="item">{{ priorityLabels[item] }}</option></select>
      <select v-model="filters.department"><option value="">全部部门</option><option v-for="item in meta.departments" :key="item">{{ item }}</option></select>
      <select v-model="filters.category"><option value="">全部类型</option><option v-for="item in meta.categories" :key="item">{{ item }}</option></select>
      <button class="button text" @click="resetFilters">重置</button>
    </section>

    <section class="panel table-panel">
      <div v-if="error" class="alert error">{{ error }}</div>
      <div class="table-scroll">
        <table>
          <thead><tr><th>工单编号</th><th>问题</th><th>部门/类型</th><th>优先级</th><th>状态</th><th>负责人</th><th>创建时间</th></tr></thead>
          <tbody>
            <tr v-if="loading"><td colspan="7" class="empty-row">正在加载…</td></tr>
            <tr v-else-if="!tickets.length"><td colspan="7" class="empty-row">没有符合条件的工单</td></tr>
            <tr v-for="ticket in tickets" :key="ticket.id" class="clickable" @click="emit('open-ticket', ticket.id)">
              <td><strong class="ticket-no">{{ ticket.ticket_no }}</strong></td>
              <td><strong>{{ ticket.title }}</strong><small>{{ ticket.description }}</small></td>
              <td>{{ ticket.department }}<small>{{ ticket.category }}</small></td>
              <td><span :class="['priority-chip', ticket.priority.toLowerCase()]">{{ priorityLabels[ticket.priority] }}</span></td>
              <td><span :class="['status-chip', ticket.status.toLowerCase()]">{{ statusLabels[ticket.status] }}</span></td>
              <td>{{ ticket.assignee_name || "未分配" }}</td>
              <td>{{ new Date(ticket.created_at).toLocaleDateString() }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <footer class="pagination"><span>共 {{ total }} 条，第 {{ filters.page }} 页</span><div><button class="button ghost" :disabled="filters.page <= 1" @click="changePage(-1)">上一页</button><button class="button ghost" :disabled="filters.page * filters.per_page >= total" @click="changePage(1)">下一页</button></div></footer>
    </section>
  </div>
</template>

