package test.data;

public class ExampleClass extends Object implements ExampleInterface {

    boolean field;
    private int privateField;
    protected Integer protectedField;
    public String publicField;

    public static String CONSTANT;

    public ExampleClass() {}
    public ExampleClass(String arg1) {}

    public void setPrivateField(int value) {
        this.privateField = value;
    }

    public int getPrivateField() {
        return privateField;
    }

    void method() {}
    public void imethod() {}
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