# **Debugging Mobile App Architecture Patterns: A Troubleshooting Guide**

## **1. Introduction**
Mobile app architecture patterns define how components interact, ensuring scalability, maintainability, and performance. Common patterns include **MVP (Model-View-Presenter), MVVM (Model-View-ViewModel), MVI (Model-View-Intent), Clean Architecture, and VIPER**. Poor implementation leads to issues like **performance bottlenecks, memory leaks, poor separation of concerns, and testability challenges**.

This guide covers **symptoms, root causes, fixes, tools, and prevention** for debugging mobile architecture issues.

---

## **2. Symptom Checklist**
Check these symptoms before diving into fixes:

✅ **Performance Issues**
- Freezing/lagging UI
- Slow API responses
- High CPU/memory usage
- Battery drain

✅ **Crashes & Instability**
- NullPointerException (common in MVP/MVVM)
- ANR (Application Not Responding)
- Force closes on background tasks

✅ **Poor Data Flow**
- Duplicate network requests
- UI updates from incorrect sources
- State mismatches (e.g., View does not reflect ViewModel)

✅ **Testability & Debugging Problems**
- Hard-to-read test classes
- Dependencies making mocking difficult
- Flaky tests

✅ **Maintenance Challenges**
- Codebase is hard to refactor
- Business logic spread across UI layers
- Tight coupling between components

✅ **UI/UX Anti-Patterns**
- Unnecessary UI updates (e.g., ViewModel triggers View updates too often)
- Missing error handling (e.g., no loading/error states)
- Bloated activities/fragments

---

## **3. Common Issues & Fixes (With Code)**

### **A.1. MVP (Model-View-Presenter) Issues**

#### **Issue: View Leaks Memory (Presenter holds View reference)**
**Symptom:** Memory leaks, ANR on configuration changes.
**Root Cause:** Presenters holding strong references to Views (e.g., Activities/Fragments).

**Fix:**
```kotlin
// Correct: Use WeakReference or detach View
class MyPresenter(private val view: ViewContract) {
    fun onViewDestroyed() {
        view.unbind() // Detach View in onDestroy()
    }
}

// In Fragment/Activity:
override fun onDestroy() {
    super.onDestroy()
    presenter.onViewDestroyed()
}
```

**Alternative:** Use **RxJava/EventBus** for communication without direct View binding.

---

#### **Issue: Business Logic in View Layer**
**Symptom:** Views directly handle API calls, logic is scattered.

**Fix (Separation of Concerns):**
```kotlin
// View (Fragment/Activity) only handles UI
class HomeFragment : Fragment() {
    private val presenter = HomePresenter(view = this)

    fun onButtonClick() {
        presenter.loadData()
    }
}

// Presenter delegates logic to Model
class HomePresenter(private val view: HomeView) {
    fun loadData() {
        // Calls API via Repository
        DataRepository.fetchData { result ->
            view.showResult(result)
        }
    }
}
```

---

### **A.2. MVVM (Model-View-ViewModel) Issues**

#### **Issue: Unnecessary View Updates (LiveData Observers Not Detached)**
**Symptom:** UI updates even when Fragment is paused/destroyed.

**Fix:**
```kotlin
class MyViewModel : ViewModel() {
    private val _data = MutableLiveData<String>()
    val data: LiveData<String> = _data

    fun updateData() {
        _data.value = "Updated"
    }
}

class MyFragment : Fragment() {
    private val viewModel: MyViewModel by viewModels()

    override fun onCreateView(...) {
        viewModel.data.observe(this, { newValue ->
            // Only update UI if Fragment is active
            if (isAdded) {
                textView.text = newValue
            }
        })
        return super.onCreateView(...)
    }

    // Detach observer when Fragment leaves lifecycle
    override fun onDestroyView() {
        viewModel.data.removeObserver { /*...*/ }
        super.onDestroyView()
    }
}
```

---

#### **Issue: State Management Chaos (Multiple ViewModels, Inconsistent State)**
**Symptom:** UI shows wrong data after navigation.

**Fix:** Use **Single-Source-of-Truth (Redux-like) with ViewModel Scoping**
```kotlin
class MainViewModel : ViewModel() {
    private val _uiState = MutableStateFlow(AppState.Idle)
    val uiState: StateFlow<AppState> = _uiState.asStateFlow()

    fun fetchData() {
        viewModelScope.launch {
            _uiState.value = AppState.Loading
            try {
                val data = repository.fetch()
                _uiState.value = AppState.Success(data)
            } catch (e: Exception) {
                _uiState.value = AppState.Error(e)
            }
        }
    }
}

// Use in Fragment:
lifecycleScope.launch {
    repeatOnLifecycle(Lifecycle.State.STARTED) {
        viewModel.uiState.collect { state ->
            when (state) {
                is AppState.Loading -> showProgress()
                is AppState.Success -> renderData(state.data)
                is AppState.Error -> showError(state.error)
            }
        }
    }
}
```

---

### **A.3. MVI (Model-View-Intent) Issues**

#### **Issue: View Sends Too Many Intents (Performance Issue)**
**Symptom:** High CPU usage due to rapid intent firing.

**Fix:** Debounce or throttle intents:
```kotlin
class UserViewModel : ViewModel() {
    private val _uiState = MutableStateFlow(UserState.Idle)
    val uiState: StateFlow<UserState> = _uiState.asStateFlow()

    private val _intent = MutableSharedFlow<String>()
    val intent: SharedFlow<String> = _intent.asSharedFlow()

    init {
        intent
            .debounce(300) // Wait 300ms after last intent
            .onEach { text ->
                _uiState.value = UserState.Loading
                viewModelScope.launch {
                    _uiState.value = UserState.Success(fetchUser(text))
                }
            }
            .launchIn(viewModelScope)
    }
}
```

---

### **A.4. Clean Architecture Issues**

#### **Issue: Data Layer Tightly Coupled to Network Layer**
**Symptom:** Changing API breaks app.

**Fix:** Use **Dependency Injection (Hilt/Dagger) for Repository**
```kotlin
@Module
@InstallIn(SingletonComponent::class)
object NetworkModule {
    @Provides
    fun provideApiService(): ApiService {
        return Retrofit.Builder()
            .baseUrl("https://api.example.com/")
            .addConverterFactory(GsonConverterFactory.create())
            .build()
            .create(ApiService::class.java)
    }

    @Provides
    fun provideUserRepository(api: ApiService): UserRepository {
        return UserRepositoryImpl(api)
    }
}
```

---

## **4. Debugging Tools & Techniques**

| **Tool/Tech**       | **Use Case**                                                                 |
|----------------------|-----------------------------------------------------------------------------|
| **Android Profiler** | Check memory leaks, CPU usage, and thread performance.                       |
| **LeakCanary**       | Detect View/Presenter/ViewModel memory leaks.                              |
| **Hilt Debug Logs**  | Verify DI (Dependency Injection) works correctly.                          |
| **Flutter DevTools** | Track state changes in MVVM/MVI apps.                                       |
| **Logcat Filters**   | Filter logs by tag (`ViewModel`, `Repository`).                             |
| **Unit Tests**       | Isolate business logic (JUnit + MockK/Triple).                              |
| **Espresso Tests**   | Test UI behavior (MVP/MVVM).                                                 |
| **Koin/Dagger Hilt Inspector** | Debug DI issues in Jetpack Compose.                                      |

**Example Debugging Workflow:**
1. **Use `LeakCanary`** to find memory leaks in Presenters/ViewModels.
2. **Check `Android Profiler`** for thread bottlenecks.
3. **Review logs** for `NullPointerException` in MVVM.
4. **Run unit tests** to isolate failing logic.

---

## **5. Prevention Strategies**

### **✅ Best Practices for MVP/MVVM/MVI**

| **Pattern** | **Best Practice**                                                                 |
|-------------|-----------------------------------------------------------------------------------|
| **MVP**     | Always detach View in `onDestroy()` to prevent leaks.                           |
| **MVVM**    | Use `StateFlow`/`LiveData` with lifecycle awareness.                             |
| **MVI**     | Debounce/filter intents to avoid rapid state changes.                            |
| **Clean Arch** | Keep `Domain` layer free of Android dependencies.                              |
| **Testing** | Write unit tests for `Presenter`/`ViewModel` (MockK for dependencies).           |

### **✅ Architectural Checklist**
- **[ ]** Is `View` only for UI? (No logic here!)
- **[ ]** Are `Presenter`/`ViewModel` stateless (or properly scoped)?
- **[ ]** Is `Repository` abstracted from implementation details?
- **[ ]** Are `LiveData`/`StateFlow` observers properly managed?
- **[ ]** Is DI used to avoid direct object creation?
- **[ ]** Are business rules in `Domain` layer (not API layer)?

### **✅ Code Structure Template (MVVM Example)**
```
src/
├── main/
│   ├── java/com/example/
│   │   ├── domain/       # Use cases & business rules
│   │   ├── data/         # Repository, API, DB
│   │   ├── presentation/  # ViewModel, UI components
│   │   └── di/           # Hilt/Dagger modules
```

---

## **6. Final Checklist Before Release**
✔ **Memory Leaks?** → `LeakCanary` + `Android Profiler`
✔ **ANR Issues?** → Check async tasks (Room, Coroutines, Retrofit)
✔ **State Mismatch?** → Debug `LiveData`/`StateFlow` observers
✔ **Crashes?** → Enable **Firebase Crashlytics** + **Logcat filtering**
✔ **Performance?** → Profile with **Android Profiler**

---
## **7. Conclusion**
Mobile architecture issues often stem from **poor separation of concerns, unmanaged lifecycle, or tight coupling**. By following **MVVM/MVI best practices, proper DI, and lifecycle awareness**, you can avoid 90% of debugging headaches.

**Key Takeaways:**
- **MVP:** Always detach View in `onDestroy()`.
- **MVVM:** Use `StateFlow` + `repeatOnLifecycle`.
- **MVI:** Debounce intents to prevent over-firing.
- **Clean Arch:** Keep `Domain` layer pure.
- **Debug:** LeakCanary, Profiler, and unit tests.

**Happy debugging!** 🚀