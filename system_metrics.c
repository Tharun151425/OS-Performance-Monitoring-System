#include <windows.h> 
#include <psapi.h> 
#include <pdh.h> 
#include <stdint.h> 

#define DLL_EXPORT __declspec(dllexport)

typedef struct {
    uint64_t total_physical;
    uint64_t available_physical;
    double memory_load;
    uint64_t page_fault_count;
    uint64_t peak_working_set;
    uint64_t private_usage;
    uint64_t paged_pool;
    uint64_t non_paged_pool;
    uint64_t cache_memory;
    uint64_t handle_count;
} MemoryMetrics;

typedef struct {
    double cpu_usage;
    uint64_t frequency;
    uint64_t core_count;
    uint64_t thread_count;
    uint64_t system_time;
    uint64_t user_time;
    uint64_t idle_time;
    uint64_t interrupt_time;
    uint64_t dpc_time;
    uint64_t context_switches;
} CPUMetrics;

typedef struct {
    uint64_t total_space;
    uint64_t used_space;
    uint64_t free_space;
    double read_speed;
    double write_speed;
    uint64_t read_bytes;
    uint64_t write_bytes;
    uint64_t queue_length;
    double response_time;
    uint64_t active_time;
} DiskMetrics;

static PDH_HQUERY cpuQuery = NULL;
static PDH_HCOUNTER cpuCounter = NULL;

DLL_EXPORT BOOL init_performance_counters() {
    if (PdhOpenQuery(NULL, 0, &cpuQuery) != ERROR_SUCCESS) {
        return FALSE;
    }
    
    if (PdhAddCounterA(cpuQuery, "\\Processor(_Total)\\% Processor Time", 0, &cpuCounter) != ERROR_SUCCESS) {
        PdhCloseQuery(cpuQuery);
        return FALSE;
    }
    
    PdhCollectQueryData(cpuQuery);
    return TRUE;
}

DLL_EXPORT void get_memory_metrics(MemoryMetrics* metrics) { 
    //GlobalMemoryStatusEx, GetProcessMemoryInfo
    MEMORYSTATUSEX memInfo;
    memInfo.dwLength = sizeof(MEMORYSTATUSEX);
    GlobalMemoryStatusEx(&memInfo);
    
    PROCESS_MEMORY_COUNTERS_EX pmc;
    GetProcessMemoryInfo(GetCurrentProcess(), (PROCESS_MEMORY_COUNTERS*)&pmc, sizeof(pmc));
    
    metrics->total_physical = memInfo.ullTotalPhys;
    metrics->available_physical = memInfo.ullAvailPhys;
    metrics->memory_load = memInfo.dwMemoryLoad;
    
    metrics->page_fault_count = pmc.PageFaultCount;
    metrics->peak_working_set = pmc.PeakWorkingSetSize;
    metrics->private_usage = pmc.PrivateUsage;
    
    metrics->paged_pool = 0;
    metrics->non_paged_pool = 0;
    metrics->cache_memory = 0;
    
    metrics->handle_count = GetGuiResources(GetCurrentProcess(), GR_GDIOBJECTS);
}

DLL_EXPORT void get_cpu_metrics(CPUMetrics* metrics) {
    //GetSystemInfo, GetProcessMemoryInfo
    PDH_FMT_COUNTERVALUE counterVal;
    
    PdhCollectQueryData(cpuQuery);
    PdhGetFormattedCounterValue(cpuCounter, PDH_FMT_DOUBLE, NULL, &counterVal);
    metrics->cpu_usage = counterVal.doubleValue;
    
    SYSTEM_INFO sysInfo;
    GetSystemInfo(&sysInfo);
    metrics->core_count = sysInfo.dwNumberOfProcessors;
    
    DWORD processId = GetCurrentProcessId();
    HANDLE hProcess = OpenProcess(PROCESS_QUERY_INFORMATION, FALSE, processId);
    if (hProcess != NULL) {
        PROCESS_MEMORY_COUNTERS_EX pmc;
        GetProcessMemoryInfo(hProcess, (PROCESS_MEMORY_COUNTERS*)&pmc, sizeof(pmc));
        CloseHandle(hProcess);
    }
    
    FILETIME idleTime, kernelTime, userTime;
    GetSystemTimes(&idleTime, &kernelTime, &userTime);
    
    metrics->idle_time = ((ULARGE_INTEGER*)&idleTime)->QuadPart;
    metrics->system_time = ((ULARGE_INTEGER*)&kernelTime)->QuadPart;
    metrics->user_time = ((ULARGE_INTEGER*)&userTime)->QuadPart;
    
    DWORD_PTR processAffinityMask, systemAffinityMask;
    GetProcessAffinityMask(GetCurrentProcess(), &processAffinityMask, &systemAffinityMask);
    metrics->thread_count = 0;
    for (DWORD_PTR mask = processAffinityMask; mask; mask >>= 1) {
        metrics->thread_count += mask & 1;
    }
    
    metrics->frequency = 0;
    metrics->context_switches = 0;
    metrics->interrupt_time = 0;
    metrics->dpc_time = 0;
}

DLL_EXPORT void get_disk_metrics(DiskMetrics* metrics) {
    //GetDiskFreeSpaceExA
    ULARGE_INTEGER freeBytesAvailable, totalBytes, totalFreeBytes;
    GetDiskFreeSpaceExA("C:\\", &freeBytesAvailable, &totalBytes, &totalFreeBytes);
    
    metrics->total_space = totalBytes.QuadPart;
    metrics->free_space = totalFreeBytes.QuadPart;
    metrics->used_space = totalBytes.QuadPart - totalFreeBytes.QuadPart;
    
    metrics->read_speed = 0;
    metrics->write_speed = 0;
    metrics->read_bytes = 0;
    metrics->write_bytes = 0;
    metrics->queue_length = 0;
    metrics->response_time = 0;
    metrics->active_time = 0;
}

BOOL APIENTRY DllMain(HANDLE hModule, DWORD ul_reason_for_call, LPVOID lpReserved) {
    switch (ul_reason_for_call) {
        case DLL_PROCESS_ATTACH:
            init_performance_counters();
            break;
        case DLL_PROCESS_DETACH:
            if (cpuQuery) {
                PdhCloseQuery(cpuQuery);
            }
            break;
    }
    return TRUE;
}