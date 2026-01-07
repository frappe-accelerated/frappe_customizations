<template>
  <div
    v-if="isMobile"
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
  <embed
    v-else
    :key="pdfKey"
    ref="embed"
    :src="srcWithCacheBust"
    type="application/pdf"
    class="w-full h-full max-h-[80vh] max-w-[80vw] self-center"
  />
</template>

<script setup>
import { computed, ref, watch, onMounted } from "vue"
import { Button, LoadingIndicator } from "frappe-ui"
import { breakpointsTailwind, useBreakpoints } from "@vueuse/core"
import { VuePDF, usePDF } from "@tato30/vue-pdf"
import "@tato30/vue-pdf/style.css"

const breakpoints = useBreakpoints(breakpointsTailwind)
const isMobile = breakpoints.smaller("sm")

const props = defineProps({
  previewEntity: Object,
})

const pdfKey = ref(Date.now())

const src = computed(
  () =>
    `/api/method/drive.api.files.get_file_content?entity_name=${props.previewEntity.name}`
)

// Add cache-busting parameter to prevent browser caching issues
const srcWithCacheBust = computed(() => {
  return `${src.value}&_t=${pdfKey.value}`
})

// Mobile PDF viewer state
const page = ref(1)
const scale = ref(1)
const pdf = ref(null)
const pages = ref(0)

const initPdf = () => {
  pdfKey.value = Date.now()
  page.value = 1
  scale.value = 1

  if (isMobile.value) {
    const pdfData = usePDF(src.value)
    pdf.value = pdfData.pdf
    pages.value = pdfData.pages
  }
}

onMounted(initPdf)

// Watch for entity changes
watch(
  () => props.previewEntity?.name,
  (newVal, oldVal) => {
    if (newVal && newVal !== oldVal) {
      initPdf()
    }
  },
  { immediate: false }
)
</script>
