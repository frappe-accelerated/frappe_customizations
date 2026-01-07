<template>
  <!-- LibreOffice-based PDF preview (replaces Microsoft external service) -->
  <div v-if="loading" class="flex items-center justify-center h-full w-full">
    <div class="text-center">
      <LucideLoader2 class="size-8 animate-spin mx-auto mb-2" />
      <span class="text-ink-gray-7">Converting document...</span>
    </div>
  </div>

  <!-- Mobile view with VuePDF -->
  <div
    v-else-if="pdfUrl && isMobile"
    class="flex flex-col gap-3 w-96 h-full justify-between grow"
  >
    <div class="flex gap-2 justify-center items-center">
      <Button
        @click="scale = scale > 0.25 ? scale - 0.25 : scale"
        :disabled="scale == 0.25"
        label="-"
      />
      <span class="text-sm">{{ scale * 100 }}%</span>
      <Button
        @click="scale = scale < 2 ? scale + 0.25 : scale"
        :disabled="scale == 2"
        label="+"
      />
    </div>
    <div class="grow flex items-center border rounded-sm max-h-[70vh]">
      <VuePDF
        :key="pdfKey"
        class="rounded-sm overflow-y-auto overflow-x-auto w-full h-full"
        :pdf
        :page
        :scale
        :text-layer="true"
      >
        <LoadingIndicator class="w-10 text-neutral-100 mx-auto h-full" />
      </VuePDF>
    </div>
    <div
      v-if="pages"
      class="flex gap-2 justify-center items-center"
    >
      <Button
        label="Prev"
        @click="page = page > 1 ? page - 1 : page"
      />
      <span class="text-sm">{{ page }} / {{ pages }}</span>
      <Button
        label="Next"
        @click="page = page < pages ? page + 1 : page"
      />
    </div>
  </div>

  <!-- Desktop view with embed -->
  <embed
    v-else-if="pdfUrl"
    :key="pdfKey"
    :src="pdfUrlWithCacheBust"
    type="application/pdf"
    class="w-full h-full max-h-[80vh] max-w-[80vw] self-center"
  />

  <!-- Error state -->
  <div
    v-else-if="error"
    class="max-w-[450px] h-fit self-center p-10 bg-surface-white rounded-md text-neutral-100 text-xl text-center font-medium shadow-xl flex flex-col justify-center items-center gap-4"
  >
    <LucideAlertCircle class="size-10" />
    <span class="text-ink-gray-8">Preview unavailable</span>
    <span class="text-p-base text-center text-ink-gray-7">{{ error }}</span>
    <Button class="w-full" variant="solid" @click="download">
      Download
    </Button>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from "vue"
import { Button, LoadingIndicator } from "frappe-ui"
import { breakpointsTailwind, useBreakpoints } from "@vueuse/core"
import { VuePDF, usePDF } from "@tato30/vue-pdf"
import "@tato30/vue-pdf/style.css"
import LucideLoader2 from "~icons/lucide/loader-2"
import LucideAlertCircle from "~icons/lucide/alert-circle"

const breakpoints = useBreakpoints(breakpointsTailwind)
const isMobile = breakpoints.smaller("sm")

const props = defineProps({
  previewEntity: Object,
})

const loading = ref(true)
const pdfUrl = ref(null)
const error = ref(null)
const pdfKey = ref(Date.now()) // Key for forcing re-render

// Mobile PDF viewer state
const page = ref(1)
const scale = ref(1)
const pdf = ref(null)
const pages = ref(0)

// Add cache-busting parameter to prevent browser caching issues
const pdfUrlWithCacheBust = computed(() => {
  if (!pdfUrl.value) return null
  const separator = pdfUrl.value.includes('?') ? '&' : '?'
  return `${pdfUrl.value}${separator}_t=${pdfKey.value}`
})

const convertDocument = async () => {
  // Reset all state
  loading.value = true
  error.value = null
  pdfUrl.value = null
  page.value = 1
  scale.value = 1
  pdf.value = null
  pages.value = 0
  pdfKey.value = Date.now() // Generate new key to force re-render

  try {
    const res = await fetch(
      `/api/method/frappe_customizations.services.document_preview.convert_drive_file?entity_name=${props.previewEntity.name}`
    )
    const data = await res.json()
    if (data.message?.success) {
      pdfUrl.value = data.message.pdf_url

      // Initialize PDF viewer for mobile
      if (isMobile.value) {
        const pdfData = usePDF(data.message.pdf_url)
        pdf.value = pdfData.pdf
        pages.value = pdfData.pages
      }
    } else {
      error.value = data.message?.error || "Failed to convert document"
    }
  } catch (e) {
    error.value = "Failed to convert document: " + e.message
  } finally {
    loading.value = false
  }
}

onMounted(convertDocument)

// Watch for changes with immediate and deep options
watch(
  () => props.previewEntity?.name,
  (newVal, oldVal) => {
    if (newVal && newVal !== oldVal) {
      convertDocument()
    }
  },
  { immediate: false }
)

const download = () => {
  window.location.href = `/api/method/drive.api.files.get_file_content?entity_name=${props.previewEntity.name}&trigger_download=1`
}
</script>
