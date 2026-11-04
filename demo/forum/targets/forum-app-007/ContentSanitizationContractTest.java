package local.aeion.forum;

import static io.restassured.RestAssured.given;
import static org.hamcrest.Matchers.equalTo;
import static org.junit.jupiter.api.Assertions.*;

import io.quarkus.test.common.WithTestResource;
import io.quarkus.test.junit.QuarkusTest;
import io.restassured.http.ContentType;
import jakarta.inject.Inject;
import java.io.StringReader;
import java.lang.reflect.InvocationTargetException;
import java.nio.charset.StandardCharsets;
import java.sql.Connection;
import java.util.List;
import java.util.Map;
import java.util.Set;
import javax.sql.DataSource;
import javax.xml.parsers.DocumentBuilderFactory;
import org.junit.jupiter.api.Test;
import org.w3c.dom.Element;
import org.xml.sax.InputSource;

/** Supervisor-owned acceptance, injected only after the candidate has answered. */
@QuarkusTest
@WithTestResource(QuarkusTestDatabase.class)
class ContentSanitizationContractTest {
    @Inject DataSource dataSource;
    @Inject ThreadService threads;

    private String[] signIn() {
        String name = "sanitize-" + System.nanoTime();
        Map<String, String> body = Map.of("username", name, "password", "synthetic-contract-password-42");
        given().contentType(ContentType.JSON).body(body).post("/api/auth/register")
                .then().statusCode(201);
        var login = given().contentType(ContentType.JSON).body(body).post("/api/auth/login")
                .then().statusCode(200).extract();
        return new String[] {login.cookie(AuthService.COOKIE), login.path("csrf")};
    }

    private Map<String, Object> create(String[] session, String body) {
        return given().cookie(AuthService.COOKIE, session[0]).header("X-CSRF-Token", session[1])
                .contentType(ContentType.JSON).body(Map.of("title", "Sanitization contract", "body", body))
                .post("/api/threads").then().statusCode(201).extract().as(Map.class);
    }

    private String safeHtml(Map<String, Object> response) throws Exception {
        Object value = response.get("body_html");
        assertInstanceOf(String.class, value, "body_html must be present");
        String html = (String) value;
        assertTrue(html.getBytes(StandardCharsets.UTF_8).length <= 32768);
        var factory = DocumentBuilderFactory.newInstance();
        factory.setFeature("http://apache.org/xml/features/disallow-doctype-decl", true);
        factory.setFeature("http://xml.org/sax/features/external-general-entities", false);
        factory.setFeature("http://xml.org/sax/features/external-parameter-entities", false);
        var document = factory.newDocumentBuilder().parse(new InputSource(new StringReader("<root>" + html + "</root>")));
        var elements = document.getDocumentElement().getElementsByTagName("*");
        Set<String> allowed = Set.of("p", "strong", "em", "ul", "ol", "li", "blockquote", "pre", "code");
        for (int i = 0; i < elements.getLength(); i++) {
            Element element = (Element) elements.item(i);
            assertTrue(allowed.contains(element.getTagName()), "unsafe element");
            assertEquals(0, element.getAttributes().getLength(), "attributes are forbidden");
        }
        return html;
    }

    @Test
    void thirtyHostilePayloadsStayInertAcrossCreateReadAndList() throws Exception {
        List<String> payloads = List.of(
                "<script>alert(1)</script>", "<img src=x onerror=alert(1)>",
                "<svg onload=alert(1)>", "<iframe src=\"https://example.invalid\"></iframe>",
                "<a href=\"javascript:alert(1)\">x</a>", "[x](javascript:alert(1))",
                "![x](https://example.invalid/x)", "<object data=x>", "<embed src=x>",
                "<style>@import 'https://example.invalid';</style>",
                "<div onclick=alert(1)>x</div>", "<body onload=alert(1)>",
                "<input autofocus onfocus=alert(1)>", "<video><source onerror=alert(1)></video>",
                "<math href=\"javascript:alert(1)\">x</math>", "<details open ontoggle=alert(1)>",
                "<form action=\"https://example.invalid\"><button>x</button></form>",
                "<meta http-equiv=refresh content=0;url=https://example.invalid>",
                "<link rel=stylesheet href=https://example.invalid/x>", "<base href=https://example.invalid>",
                "<!--><script>alert(1)</script>-->", "<sCrIpT>alert(1)</sCrIpT>",
                "&lt;script&gt;alert(1)&lt;/script&gt;", "<img src=x/onerror=alert(1)>",
                "<a href=\"data:text/html,<script>alert(1)</script>\">x</a>",
                "<svg><a xlink:href=\"javascript:alert(1)\">x</a></svg>",
                "<div style=\"background:url(https://example.invalid/x)\">x</div>",
                "</code></pre><script>alert(1)</script>", "<textarea></textarea><script>x</script>",
                "<script src=//example.invalid/x></script>");
        assertEquals(30, payloads.size());
        String[] session = signIn();
        for (String payload : payloads) {
            var created = create(session, payload);
            String html = safeHtml(created);
            var read = given().get("/api/threads/" + created.get("id")).then().statusCode(200)
                    .extract().as(Map.class);
            assertEquals(html, safeHtml(read));
        }
        List<Map<String, Object>> listed = given().get("/api/threads?limit=100").then().statusCode(200)
                .extract().path("threads");
        for (var item : listed) safeHtml(item);
    }

    @Test
    void normalizedMarkdownIsStoredAndRenderingIsStable() throws Exception {
        String raw = "  Cafe\u0301 \u0000\u200b  monde \r\n\r\n  ligne  ";
        var created = create(signIn(), raw);
        String expected = "Café monde\n\nligne";
        assertEquals(expected, created.get("body"));
        assertEquals("<p>Café monde</p>\n<p>ligne</p>", safeHtml(created));
        try (Connection connection = dataSource.getConnection();
             var query = connection.prepareStatement("SELECT body FROM threads WHERE id = ?")) {
            query.setString(1, (String) created.get("id"));
            try (var row = query.executeQuery()) {
                assertTrue(row.next());
                assertEquals(expected, row.getString(1));
            }
        }
        var repeated = create(signIn(), expected);
        assertEquals(expected, repeated.get("body"));
        assertEquals(created.get("body_html"), repeated.get("body_html"));
    }

    @Test
    void theSmallMarkdownSubsetHasExactSafeOutput() throws Exception {
        String[] session = signIn();
        Map<String, String> fixtures = Map.of(
                "Bonjour **monde** et *ami*", "<p>Bonjour <strong>monde</strong> et <em>ami</em></p>",
                "- un\n- deux", "<ul><li>un</li><li>deux</li></ul>",
                "1. un\n2. deux", "<ol><li>un</li><li>deux</li></ol>",
                "> bonjour\n> monde", "<blockquote><p>bonjour monde</p></blockquote>",
                "```java\n  <x>  \n```", "<pre><code>  &lt;x&gt;  \n</code></pre>",
                "```\n**literal** & <x>\n```", "<pre><code>**literal** &amp; &lt;x&gt;\n</code></pre>");
        for (var entry : fixtures.entrySet()) {
            assertEquals(entry.getValue(), safeHtml(create(session, entry.getKey())));
        }
        assertEquals("<p>&lt;script&gt;x&lt;/script&gt;</p>",
                safeHtml(create(session, "<script>x</script>")));
    }

    @Test
    void oversizeContentIs413AndNeverAddsAnOutboxRow() {
        String[] session = signIn();
        long before = threads.pendingCount();
        given().cookie(AuthService.COOKIE, session[0]).header("X-CSRF-Token", session[1])
                .contentType(ContentType.JSON)
                .body(Map.of("title", "Oversize content", "body", "x".repeat(4001)))
                .post("/api/threads").then().statusCode(413)
                .body("error", equalTo("content_too_large"));
        assertEquals(before, threads.pendingCount());
    }

    @Test
    void codepointBoundsDoNotMistakeSupplementaryUnicodeForTwoCharacters() throws Exception {
        var sanitizer = Class.forName("local.aeion.forum.ContentSanitizer");
        var sanitize = sanitizer.getMethod("sanitize", String.class);
        String boundary = "😀".repeat(4000);
        Object result = sanitize.invoke(null, boundary);
        assertEquals(boundary, result.getClass().getMethod("markdown").invoke(result));
        var failure = assertThrows(InvocationTargetException.class,
                () -> sanitize.invoke(null, boundary + "x"));
        assertEquals("ContentTooLargeException", failure.getCause().getClass().getSimpleName());
        assertEquals("content_too_large", failure.getCause().getMessage());
        assertThrows(InvocationTargetException.class, () -> sanitize.invoke(null, "\u0000".repeat(4001)));
    }
}
