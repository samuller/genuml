package test.data;

public interface ExampleInterface {

    void imethod();
    private int privateMethod() {
        return 0;
    }
    public String publicMethod();

    default public Integer defaultMethod() {
        return 0;
    }
}