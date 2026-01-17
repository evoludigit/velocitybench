**[Pattern] Mobile App Architecture Patterns – Reference Guide**

---

### **1. Overview**
Mobile app architecture defines how components interact, data flows, and business logic is organized. Well-structured architectures enhance maintainability, scalability, and testability. This guide covers five core mobile architecture patterns—**MVC, MVVM, MVP, Clean Architecture, and VIPER**—including their key components, trade-offs, and implementation considerations. Each pattern addresses different needs (e.g., separation of concerns, testability) while adapting to iOS/Android constraints (e.g., UI frameworks, lifecycle management).

---

### **2. Schema Reference**
Compare patterns using the table below for quick reference.

| **Pattern**       | **Separation of Concerns**               | **Data Flow**                     | **Testability**                     | **Use Case**                          | **Key Libraries/Tools**               |
|-------------------|----------------------------------------|-----------------------------------|-------------------------------------|---------------------------------------|--------------------------------------|
| **MVC**          | Model (data), View (UI), Controller (logic) | View → Controller → Model → View | Moderate (controllers can be tested) | Simple apps, rapid prototyping         | UIKit (iOS), Android ViewModel       |
| **MVVM**         | Model, View, ViewModel (logic + bindings) | View ↔ ViewModel ↔ Model          | High (ViewModels can be mocked)     | Complex UIs, data-driven apps         | Core Data, Realm (iOS); LiveData (Android) |
| **MVP**          | Model, View (dumb), Presenter (logic)  | View → Presenter → Model → View   | High (Presenters can be tested)     | Legacy apps, test-heavy workflows      | Robolectric (Android), UI Tests      |
| **Clean**        | Domain (business logic), UI, Data, Framework | Unidirectional: UI → Use Cases → Repo → Data → UI | Very high (layered dependencies)   | Enterprise apps, large teams          | Dependency injection (DI), RxJava/Kotlin Coroutines |
| **VIPER**        | View, Interactor, Presenter, Entity, Router, Use Case | Cyclical but scoped per module    | High (interactors can be mocked)    | Modular apps, scalable architectures   | Object-Oriented design, DI frameworks |

---

### **3. Pattern Details**

---

#### **A. MVC (Model-View-Controller)**
**Purpose:**
Separates user interface (View), data (Model), and logic (Controller) to improve maintainability.

**Key Components:**
| Component       | Role                                                                 | Example (iOS/Android)                          |
|-----------------|----------------------------------------------------------------------|-----------------------------------------------|
| **Model**       | Manages data (e.g., API calls, databases).                           | Core Data (iOS), Room (Android)               |
| **View**        | Renders UI; sends user actions to Controller.                         | UIKit (iOS), Jetpack Compose (Android)         |
| **Controller**  | Handles user input, updates Model/View.                              | SwiftUI `ViewController`, Android `Activity`   |

**Implementation Notes:**
- **Data Binding:** Views communicate via delegates or callbacks.
- **Lifecycle:** Controllers manage UI state changes (e.g., `viewDidLoad` in iOS).
- **Testing:** Mock Models for unit tests; UI Tests for Controller-View integration.

**Example Flow (iOS):**
```swift
// View (UIViewController)
class LoginVC: UIViewController, LoginVCDelegate {
    func onLoginSuccess() {
        // Update UI
    }
}

// Controller
class LoginController {
    private let model: LoginModel
    weak var viewDelegate: LoginVCDelegate?

    func login(email: String, password: String) {
        model.login { [weak self] result in
            self?.viewDelegate?.onLoginSuccess()
        }
    }
}
```

**Trade-offs:**
✅ Simple for small apps.
❌ Tight coupling between View and Controller; hard to test Views.

---

#### **B. MVVM (Model-View-ViewModel)**
**Purpose:**
Enhances MVC by decoupling View from logic via **two-way data binding**.

**Key Components:**
| Component       | Role                                                                 | Example (iOS/Android)                          |
|-----------------|----------------------------------------------------------------------|-----------------------------------------------|
| **View**        | Displays data; binds to ViewModel properties.                        | SwiftUI `@StateObject`, Android `LiveData`     |
| **ViewModel**   | Contains business logic; exposes observable data.                    | Combine (iOS), ViewModel (Android)             |
| **Model**       | Raw data (e.g., API responses).                                     | Core Data, Room                                 |

**Implementation Notes:**
- **Binding:** Views observe ViewModel properties (e.g., `@Published` in Combine).
- **Lifecycle:** ViewModels live longer than Views (e.g., `ViewModelProvider` in Android).
- **Testing:** ViewModels can be tested in isolation.

**Example Flow (iOS/SwiftUI):**
```swift
// ViewModel
class UserViewModel: ObservableObject {
    @Published var user: User?
    private let userService: UserService

    func fetchUser() {
        userService.getUser { [weak self] user in
            self?.user = user
        }
    }
}

// View
struct UserView: View {
    @StateObject var viewModel = UserViewModel()
    var body: some View {
        Text("Loading...")
            .onAppear { viewModel.fetchUser() }
        // Auto-updates when `user` changes
    }
}
```

**Trade-offs:**
✅ Strong separation; test-friendly.
❌ Overhead for simple apps; steep learning curve for bindings.

---

#### **C. MVP (Model-View-Presenter)**
**Purpose:**
Reduces coupling by pushing logic to a **Presenter**, which acts as a middleman.

**Key Components:**
| Component       | Role                                                                 | Example (iOS/Android)                          |
|-----------------|----------------------------------------------------------------------|-----------------------------------------------|
| **View**        | Dumb; delegates actions to Presenter.                                | Protocol-driven (e.g., `LoginViewProtocol`)    |
| **Presenter**   | Handles business logic; updates View via callbacks.                 | Swift, Android (MVP frameworks like MVP Architecture) |
| **Model**       | Manages data (same as MVC).                                         | Core Data, Retrofit                             |

**Implementation Notes:**
- **Unidirectional Flow:** View → Presenter → Model → View.
- **Testing:** Presenters can be mocked for unit tests.
- **Lifecycle:** Presenters survive View changes (e.g., `viewWillAppear`).

**Example Flow (Android):**
```kotlin
// View (Activity/Fragment)
class LoginActivity : AppCompatActivity(), LoginView {
    private lateinit var presenter: LoginPresenter

    override fun onCreate(savedInstanceState: Bundle?) {
        presenter = LoginPresenter(this)
    }

    // Delegate methods
    override fun showError(message: String) {
        Toast.makeText(this, message, Toast.LENGTH_SHORT).show()
    }
}

// Presenter
class LoginPresenter(private val view: LoginView) {
    fun login(email: String, password: String) {
        val result = apiService.login(email, password)
        if (result.isSuccess) {
            view.navigateToHome()
        } else {
            view.showError(result.error)
        }
    }
}
```

**Trade-offs:**
✅ Clear separation; easier to test than MVC.
❌ More boilerplate for callbacks.

---

#### **D. Clean Architecture**
**Purpose:**
Decouples business logic from external concerns (UI, data sources) using **layers**.

**Key Components:**
| Layer          | Responsibility                                              | Example Architecture                     |
|----------------|------------------------------------------------------------|----------------------------------------|
| **Domain**     | Business rules (entities, use cases).                      | Pure Swift/Kotlin (no frameworks)      |
| **Data**       | Data sources (APIs, databases).                            | Repository pattern, DataMapper          |
| **UI**         | Presentation layer (views, view models).                    | SwiftUI, Jetpack Compose                |
| **Framework**  | External dependencies (e.g., Android/iOS SDKs).            | DI, EventBus (e.g., RxJava)            |

**Implementation Notes:**
- **Dependency Rule:** Inner layers **depend on** outer layers (e.g., UI calls Data → Domain).
- **Testing:** Domain layer can be tested without UI/Data.
- **Tools:** Use **dependency injection** (e.g., Dagger, Swift’s `DIContainer`).

**Example Flow:**
```swift
// Domain Layer (pure Swift)
protocol GetUserUseCase {
    func execute() -> User
}

// Data Layer
class UserRepository {
    func fetchUser() -> User {
        // Calls API/database
    }
}

// UI Layer
class UserViewModel {
    private let getUserUseCase: GetUserUseCase
    init(getUserUseCase: GetUserUseCase) {
        self.getUserUseCase = getUserUseCase
    }

    func loadUser() {
        let user = getUserUseCase.execute()
        // Update UI
    }
}
```

**Trade-offs:**
✅ Highly testable; scalable for large apps.
❌ Complex setup; overkill for small projects.

---

#### **E. VIPER (Viola!)**
**Purpose:**
Modularizes apps into **interchangeable modules** (each following MVP principles).

**Key Components:**
| Component       | Role                                                                 | Example (iOS)                          |
|-----------------|----------------------------------------------------------------------|---------------------------------------|
| **View**        | Handles UI; delegates to Interactor.                                | `UIKit ViewController`                |
| **Interactor**  | Core logic (business use cases).                                    | `LoginInteractor`                     |
| **Presenter**   | Mediates between View and Interactor.                               | `LoginPresenter`                      |
| **Entity**      | Data structure (e.g., `User`).                                     | Swifty JSON models                     |
| **Router**      | Navigation logic.                                                   | `LoginRouter`                         |
| **Use Case**    | Specific task (e.g., `login`).                                     | `LoginUseCase`                         |

**Implementation Notes:**
- **Module Scoping:** Each VIPER module is self-contained.
- **Testing:** Interactors can be mocked.
- **Navigation:** Router handles transitions (e.g., `pushViewController`).
- **Tools:** Combine with **dependency injection** (e.g., `swinject`).

**Example Workflow (iOS):**
```swift
// Interactor
class LoginInteractor: LoginInteractorInput {
    weak var presenter: LoginInteractorOutput?
    private let userService: UserService

    func login(email: String, password: String) {
        userService.login(email: email, password: password) { result in
            switch result {
            case .success: self.presenter?.didLoginSuccess()
            case .failure: self.presenter?.didLoginFail(error: result.error)
            }
        }
    }
}

// Presenter (links View ↔ Interactor)
class LoginPresenter: LoginInteractorOutput {
    weak var view: LoginPresentationProtocol?

    func didLoginSuccess() {
        view?.showMainTabBar()
    }
}
```

**Trade-offs:**
✅ Highly modular; great for large apps.
❌ Verbose; steep learning curve.

---

### **4. Query Examples**
#### **Swapping Patterns in a Project**
**Scenario:** Migrate an MVC app to MVVM.
**Steps:**
1. **Extract Logic:**
   ```swift
   // Old: Controller logic in ViewController
   class LoginVC: UIViewController {
       func login() { /* ... */ } // Move to ViewModel
   }
   ```
2. **Create ViewModel:**
   ```swift
   class LoginViewModel: ObservableObject {
       @Published var isLoading = false
       private let service: AuthService

       func login(email: String, password: String) {
           isLoading = true
           service.login(email: email, password: password) { [weak self] result in
               self?.isLoading = false
               // Update published properties
           }
       }
   }
   ```
3. **Bind to View:**
   ```swift
   struct LoginView: View {
       @StateObject var viewModel = LoginViewModel()
       var body: some View {
           Button("Login") {
               viewModel.login(email: "test", password: "123")
           }
           .disabled(viewModel.isLoading)
       }
   }
   ```

#### **Clean Architecture Dependency Injection**
**Scenario:** Inject a `UserRepository` into a `UserViewModel`.
**Code:**
```swift
// Domain Layer
protocol UserRepository {
    func fetchUser() -> User
}

// Data Layer
class ApiUserRepository: UserRepository {
    func fetchUser() -> User { /* ... */ }
}

// UI Layer
class UserViewModel {
    private let repository: UserRepository

    init(repository: UserRepository) {
        self.repository = repository
    }

    func loadUser() {
        let user = repository.fetchUser()
        // Update view
    }
}

// DI Setup (e.g., in AppDelegate)
let repository = ApiUserRepository()
let viewModel = UserViewModel(repository: repository)
```

---

### **5. Related Patterns**
| **Pattern**               | **Connection to Mobile Architecture**                                                                 | **When to Use**                          |
|---------------------------|-----------------------------------------------------------------------------------------------------|------------------------------------------|
| **Repository Pattern**    | Used in **Clean Architecture** and **MVVM** to abstract data sources (APIs, databases).             | When you need to swap data layers (e.g., mock for tests). |
| **Single Responsibility Principle (SRP)** | Applies to **all patterns**; each class/module should do one thing (e.g., `Presenter` handles logic). | Improves maintainability.               |
| **Dependency Injection (DI)** | Critical for **Clean Architecture** and **VIPER**; decouples dependencies (e.g., inject `AuthService`). | Avoids tight coupling in large apps.     |
| **MVU (Model-View-Update)** | Alternative to MVVM; updates state via events (e.g., **Swift’s Combine** or **Redux**).            | Complex state management (e.g., games). |
| **CQRS (Command Query Responsibility Segregation)** | Separates read (queries) and write (commands) operations in **Clean Architecture**.          | High-performance apps with heavy reads.  |
| **Modularization**        | Core to **VIPER**; apps are divided into reusable modules.                                          | Large-scale apps with teams.            |

---

### **6. Decision Guide**
| **Priority**          | **Choose This Pattern If…**                                                                 |
|-----------------------|-------------------------------------------------------------------------------------------|
| **Simplicity**        | **MVC** for small apps or rapid prototyping.                                              |
| **Testability**       | **MVP** or **MVVM** (MVP for legacy, MVVM for data binding).                               |
| **Scalability**       | **Clean Architecture** for enterprise apps.                                                |
| **Modularity**        | **VIPER** for large, team-driven projects.                                                 |
| **Data-Driven UI**    | **MVVM** with **Combine** (iOS) or **LiveData** (Android).                                |

---
**Note:** Combine patterns where needed. For example:
- Use **MVVM + Clean Architecture** to separate UI logic from business rules.
- Add **VIPER modules** to a **Clean Architecture** app for team isolation.