# **[Pattern] Deep Linking Patterns – Reference Guide**

---

## **Overview**
Deep linking enables users to navigate directly to specific content, actions, or workflows within an app or platform by using custom URLs (deep links). Unlike standard URLs that land users on a homepage, deep links target precise destinations (e.g., `myapp://product/12345`). This pattern is critical for seamless user experience, cross-platform redirects, and app engagement. Implementing deep links efficiently requires defining clear **link schemas**, handling edge cases (e.g., app installs, redirects), and ensuring compatibility with mobile/desktop environments.

This guide covers **schema design**, **link validation**, **fallback mechanisms**, and **integration examples** to help developers and designers build robust deep linking systems.

---

## **Key Concepts**

### **1. Deep Linking Components**
| Component          | Description                                                                 |
|--------------------|-----------------------------------------------------------------------------|
| **Uniform Resource Identifier (URI)** | The full deep link (e.g., `myapp://profile?id=42`).                       |
| **Link Schema**    | The protocol prefix (e.g., `myapp://`). Must be registered with the OS.    |
| **Path Segments**  | Hierarchical segments (e.g., `/products/`).                               |
| **Query Parameters** | Key-value pairs (e.g., `?utm_source=email`).                              |
| **Fragment (#)**   | Secondary navigation (e.g., `#reviews`).                                   |
| **Fallback URL**   | Non-app URL to redirect users if the app isn’t installed.                 |

### **2. Deep Linking Types**
| Type               | Description                                                                 | Example                          |
|--------------------|-----------------------------------------------------------------------------|----------------------------------|
| **Universal Links (iOS/Android)** | OS-level links that open in the app or browser. Requires HTTPS.          | `https://example.com/product/5`  |
| **Custom Scheme**  | Legacy app-only links (e.g., `myapp://`). Requires app registration.        | `myapp://settings/profile`        |
| **Associated Domains (iOS)** | Extends domain access to custom schemes for deeper integration.             | `myapp.com → myapp://`           |
| **Intent Filters (Android)** | Declares app’s deep link handling capabilities in the manifest.              | `<intent-filter android:autoVerify="true">` |

---

## **Schema Reference**
Define your deep link structure using the following schema for consistency.

| Field            | Type         | Required | Description                                                                 | Example Value           |
|------------------|--------------|----------|-----------------------------------------------------------------------------|-------------------------|
| **Protocol**     | String       | Yes      | App’s custom scheme or `https` for universal links.                        | `myapp://`, `https://`   |
| **Base Path**    | String       | No       | Root directory (e.g., `/users`).                                           | `/products`             |
| **Segment 1**    | String       | No       | First identifier (e.g., `login`, `profile`).                              | `profile`               |
| **Segment 2**    | String       | No       | Secondary identifier (e.g., `id`).                                         | `id`                    |
| **Query Key**    | String       | No       | Parameter name (e.g., `utm_source`).                                       | `utm_source`            |
| **Fallback URL** | String       | No       | Web URL for non-app users.                                                 | `https://example.com`   |

---
**Example Schema:**
```
myapp://products/{id}?category={category}&utm_source={utm_source}
```
- **Segment 1:** `products`
- **Segment 2 (ID):** `{id}` (numeric or alphanumeric)
- **Query Keys:** `category`, `utm_source`
- **Fallback:** `https://example.com/products/{id}`

---

## **Implementation Details**

### **1. Registering Custom Schemes**
- **iOS**: Add to `Info.plist`:
  ```xml
  <key>CFBundleURLTypes</key>
  <array>
    <dict>
      <key>CFBundleURLSchemes</key>
      <array>
        <string>myapp</string>
      </array>
    </dict>
  </array>
  ```
- **Android**: Declare in `AndroidManifest.xml`:
  ```xml
  <intent-filter>
    <action android:name="android.intent.action.VIEW" />
    <category android:name="android.intent.category.DEFAULT" />
    <category android:name="android.intent.category.BROWSABLE" />
    <data android:scheme="myapp" />
  </intent-filter>
  ```

### **2. Parsing and Handling Deep Links**
#### **iOS (Swift)**
```swift
if let url = URL(string: "myapp://product/12345") {
    let scheme = url.scheme
    let path = url.pathComponents
    // Handle path segments (e.g., pathComponents[2] = "12345")
}
```

#### **Android (Kotlin)**
```kotlin
val intent = Intent(Intent.ACTION_VIEW, Uri.parse("myapp://product/12345"))
if (intent.resolveActivity(packageManager) != null) {
    startActivity(intent)
}
```

### **3. Fallback Mechanism**
If the app isn’t installed, redirect to:
```html
<a href="https://play.google.com/store/apps/details?id=com.example.myapp">
  Install App →
</a>
```

### **4. Query Parameter Validation**
```swift
guard let id = URLQueryItem(name: "id", value: pathQuery["id"]) else {
    return // Handle error
}
```

---

## **Query Examples**

### **1. Product Page Deep Link**
- **Deep Link:** `myapp://products/12345?category=electronics`
- **Fallback:** `https://example.com/products/12345?category=electronics`

### **2. User Profile Deep Link**
- **Deep Link:** `myapp://profile?user_id=abc123&lang=en`
- **Fallback:** `https://example.com/users/abc123`

### **3. Checkout Flow (with Session Token)**
- **Deep Link:** `myapp://checkout?token=xyz789&amount=99.99`
- **Fallback:** `https://example.com/checkout?token=xyz789`

### **4. Universal Link (iOS/Android)**
- **Deep Link:** `https://example.com/app/products/12345`
- **App Target:** `myapp://products/12345`

---

## **Best Practices**
1. **Use HTTPS for Universal Links** to avoid security warnings.
2. **Validate Query Parameters** server-side to prevent injection attacks.
3. **Test with `x-callback-url`** (e.g., `myapp://callback?success=true`).
4. **Support App Updates** by checking for newer versions on fallback redirects.
5. **Log Deep Link Events** for analytics (e.g., click-through rates).

---

## **Error Handling & Edge Cases**

| Scenario                     | Solution                                                                 |
|-------------------------------|--------------------------------------------------------------------------|
| App not installed             | Redirect to app store/fallback URL.                                     |
| Invalid path segment          | Show 404 or default page.                                               |
| Missing query parameter       | Default value or error prompt.                                          |
| Scheme blocked by OS          | Use universal links as fallback.                                         |
| Deep link expired (e.g., promo code) | Server-side validation. |

---

## **Related Patterns**
- **[Universal Links](https://developer.apple.com/documentation/xcode/supporting-universal-links-on-ios)** for iOS.
- **[Android App Links](https://developer.android.com/training/app-links)** for Android.
- **[OAuth Deep Links](https://auth0.com/docs/flows/deep-linking)** for authentication flows.
- **[Analytics Tracking](https://support.google.com/analytics/answer/1009684)** for deep link performance.

---
**Note:** Deep linking requires coordination between frontend, backend, and app developers. Always document schemas and test cross-platform compatibility.

---
**Word Count:** ~1,000
**Optimized for:** Scannability (tables, short paragraphs), actionable examples.