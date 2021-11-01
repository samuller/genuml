package test.data;

public abstract class ExampleAbstract implements ExampleInterface {

    boolean field;
    private int privateField;
    protected Integer protectedField;
    public String publicField;

    public static String CONSTANT;

    public ExampleAbstract() {}
    public ExampleAbstract(String arg1) {}

    public void setPrivateField(int value) {
        this.privateField = value;
    }

    public int getPrivateField() {
        return privateField;
    }

    void method() {}
    private int privateMethod() {
        return 0;
    }
    protected Integer protectedMethod() {
        return 0;
    }
    public String publicMethod() {
        return "";
    }

    public static void main(String[] args) {}
}